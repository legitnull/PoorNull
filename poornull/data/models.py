"""
Data models for market data.

Provides typed wrappers around DataFrames inspired by:
- Zipline's BarData (typed API over DataPortal)
- Lean's TradeBar (strongly-typed bar objects)
- Qlib's Provider pattern (domain-specific interfaces)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

import pandas as pd


@dataclass(frozen=True)
class Bar:
    """Single OHLCV bar - immutable."""

    date: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    @classmethod
    def from_series(cls, row: pd.Series) -> Bar:
        """Create Bar from DataFrame row."""
        return cls(
            date=pd.to_datetime(row["date"]),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=float(row["volume"]),
        )


@dataclass
class Signal:
    """Trading signal/recommendation."""

    message: str
    severity: Literal["info", "warning", "action"] = "info"
    timestamp: datetime | None = None
    metadata: dict | None = None


class PriceHistory:
    """
    Typed wrapper around DataFrame for price history.
    Provides domain methods for accessing and analyzing price data.
    """

    REQUIRED_COLUMNS = frozenset({"date", "open", "high", "low", "close", "volume"})

    def __init__(self, df: pd.DataFrame):
        """
        Initialize with DataFrame.

        Args:
            df: DataFrame with OHLCV data

        Raises:
            ValueError: If required columns missing or DataFrame empty
        """
        if df.empty:
            raise ValueError("Cannot create PriceHistory from empty DataFrame")

        self._validate_schema(df)
        self._df = df.copy().sort_values("date").reset_index(drop=True)

        self._date_index = pd.Series(self._df.index, index=pd.DatetimeIndex(self._df["date"]))
        self._cache = {}

    @classmethod
    def _validate_schema(cls, df: pd.DataFrame) -> None:
        """Validate DataFrame has required columns."""
        missing = cls.REQUIRED_COLUMNS - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}. Required: {cls.REQUIRED_COLUMNS}")

    # ===== Index-based Access =====

    @property
    def current(self) -> Bar:
        """Get the most recent bar."""
        return Bar.from_series(self._df.iloc[-1])

    def bar_at(self, index: int) -> Bar:
        """
        Get bar at specific index.

        Args:
            index: Position (negative indexing supported)

        Returns:
            Bar at that position

        Raises:
            IndexError: If index out of range
        """
        try:
            return Bar.from_series(self._df.iloc[index])
        except IndexError as e:
            raise IndexError(f"Index {index} out of range for history with {len(self)} bars") from e

    # ===== Date-based Access =====

    def on(self, date: str | datetime | pd.Timestamp) -> Bar:
        """
        Get bar for a specific date (exact match).

        Args:
            date: Date to retrieve

        Returns:
            Bar for that date

        Raises:
            KeyError: If date not found
        """
        date = pd.Timestamp(date).normalize()
        if date not in self._date_index.index:
            available = f"{self.start_date.date()} to {self.end_date.date()}"
            raise KeyError(f"Date {date.date()} not found in history. Available range: {available}")
        idx = self._date_index[date]
        return Bar.from_series(self._df.iloc[idx])

    def asof(self, date: str | datetime | pd.Timestamp) -> Bar:
        """
        Get bar as-of date (most recent bar on or before date).

        Args:
            date: Date to query

        Returns:
            Most recent bar on or before the date

        Raises:
            ValueError: If date is before earliest data
        """
        date = pd.Timestamp(date).normalize()

        if date < self._df["date"].iloc[0]:
            raise ValueError(f"Date {date.date()} is before earliest data ({self._df['date'].iloc[0].date()})")

        idx = self._df["date"].searchsorted(date, side="right") - 1
        if idx < 0:
            idx = 0
        elif idx >= len(self._df):
            idx = len(self._df) - 1

        return Bar.from_series(self._df.iloc[idx])

    def between(
        self,
        start_date: str | datetime | pd.Timestamp,
        end_date: str | datetime | pd.Timestamp,
        inclusive: Literal["both", "left", "right", "neither"] = "both",
    ) -> pd.DataFrame:
        """
        Get bars between two dates.

        Args:
            start_date: Start date
            end_date: End date
            inclusive: Include boundaries ("both", "left", "right", "neither")

        Returns:
            DataFrame with bars in date range
        """
        start = pd.Timestamp(start_date).normalize()
        end = pd.Timestamp(end_date).normalize()

        mask = pd.Series(True, index=self._df.index)

        if inclusive in ("both", "left"):
            mask &= self._df["date"] >= start
        else:
            mask &= self._df["date"] > start

        if inclusive in ("both", "right"):
            mask &= self._df["date"] <= end
        else:
            mask &= self._df["date"] < end

        return self._df[mask].copy()

    def has_date(self, date: str | datetime | pd.Timestamp) -> bool:
        """Check if specific date exists in history."""
        date = pd.Timestamp(date).normalize()
        return date in self._date_index.index

    # ===== Indicator Access =====

    def indicator(
        self, name: str, index: int | None = None, date: str | datetime | pd.Timestamp | None = None, offset: int = 0
    ) -> float | None:
        """
        Get indicator value by index, date, or offset from current.

        Args:
            name: Indicator name
            index: Absolute position (-1 for latest)
            date: Specific date
            offset: Offset from current bar (0=current, 1=previous, etc.)

        Returns:
            Indicator value or None if not available

        Examples:
            >>> history.indicator("MA250")  # Current MA250
            >>> history.indicator("MA250", offset=1)  # Previous bar's MA250
            >>> history.indicator("MA250", index=0)  # First bar's MA250
            >>> history.indicator("MA250", date="2024-01-15")  # MA250 on specific date
        """
        # Validate arguments
        args_provided = sum([index is not None, date is not None, offset != 0])
        if args_provided > 1:
            raise ValueError("Specify only one of: 'index', 'date', or 'offset'")

        if name not in self._df.columns:
            return None

        if date is not None:
            date_ts = pd.Timestamp(date).normalize()
            if date_ts not in self._date_index.index:
                return None
            idx = self._date_index[date_ts]
            val = self._df.iloc[idx][name]
        elif index is not None:
            val = self._df.iloc[index][name]
        else:
            # Use offset from current (most common case)
            idx = -1 - offset
            if abs(idx) > len(self._df):
                return None
            val = self._df.iloc[idx][name]

        return float(val) if pd.notna(val) else None

    def has_indicator(self, name: str) -> bool:
        """Check if indicator exists."""
        return name in self._df.columns

    # ===== Pattern Detection =====

    def is_above(self, indicator: str, bars: int = 1) -> bool:
        """Check if price has been above indicator for n consecutive bars."""
        if indicator not in self._df.columns or len(self._df) < bars:
            return False
        recent = self._df.tail(bars)
        return bool((recent["close"] > recent[indicator]).all())

    def is_below(self, indicator: str, bars: int = 1) -> bool:
        """Check if price has been below indicator for n consecutive bars."""
        if indicator not in self._df.columns or len(self._df) < bars:
            return False
        recent = self._df.tail(bars)
        return bool((recent["close"] < recent[indicator]).all())

    def crossed_above(self, indicator: str, within_bars: int = 1) -> bool:
        """Check if price crossed above indicator within last n bars."""
        if indicator not in self._df.columns or len(self._df) < within_bars + 1:
            return False

        window = self._df.tail(within_bars + 1)
        was_below = bool(window.iloc[0]["close"] < window.iloc[0][indicator])
        is_above = bool(window.iloc[-1]["close"] > window.iloc[-1][indicator])
        return was_below and is_above

    def crossed_below(self, indicator: str, within_bars: int = 1) -> bool:
        """Check if price crossed below indicator within last n bars."""
        if indicator not in self._df.columns or len(self._df) < within_bars + 1:
            return False

        window = self._df.tail(within_bars + 1)
        was_above = bool(window.iloc[0]["close"] > window.iloc[0][indicator])
        is_below = bool(window.iloc[-1]["close"] < window.iloc[-1][indicator])
        return was_above and is_below

    # ===== History Access =====

    def history(self, bars: int, field: str = "close") -> pd.Series:
        """Get historical data for specified field."""
        if field not in self._df.columns:
            raise KeyError(f"Field '{field}' not found")
        return self._df.tail(bars)[field].copy()

    # ===== DataFrame Access =====

    @property
    def df(self) -> pd.DataFrame:
        """Get underlying DataFrame (returns copy)."""
        return self._df.copy()

    def tail(self, n: int) -> pd.DataFrame:
        """Get last n rows."""
        return self._df.tail(n).copy()

    # ===== Metadata =====

    def __len__(self) -> int:
        return len(self._df)

    @property
    def columns(self) -> list[str]:
        return list(self._df.columns)

    @property
    def start_date(self) -> datetime:
        """First date in history."""
        return self._df["date"].iloc[0]

    @property
    def end_date(self) -> datetime:
        """Last date in history."""
        return self._df["date"].iloc[-1]

    @property
    def date_range(self) -> tuple[datetime, datetime]:
        """(start_date, end_date) tuple."""
        return (self.start_date, self.end_date)

    def __repr__(self) -> str:
        start = self.start_date.strftime("%Y-%m-%d")
        end = self.end_date.strftime("%Y-%m-%d")
        return f"PriceHistory({len(self)} bars, {start} to {end})"
