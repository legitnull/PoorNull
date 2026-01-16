"""Tests for data models (Bar, PriceHistory, Signal)."""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from poornull.data.models import Bar, PriceHistory, Signal


@pytest.fixture
def sample_df():
    """Create sample DataFrame with 10 trading days."""
    dates = pd.date_range("2024-01-01", periods=10, freq="D")
    return pd.DataFrame(
        {
            "date": dates,
            "open": np.arange(100, 110, dtype=float),
            "high": np.arange(102, 112, dtype=float),
            "low": np.arange(98, 108, dtype=float),
            "close": np.arange(101, 111, dtype=float),
            "volume": np.arange(1000, 1100, 10, dtype=float),
        }
    )


@pytest.fixture
def sample_df_with_indicators(sample_df):
    """Add indicators to sample DataFrame."""
    df = sample_df.copy()
    df["MA5"] = df["close"].rolling(5).mean()
    df["MA10"] = df["close"].rolling(10).mean()
    df["MA250"] = 95.0
    return df


class TestBar:
    """Tests for Bar dataclass."""

    def test_bar_creation(self):
        bar = Bar(date=datetime(2024, 1, 1), open=100.0, high=105.0, low=99.0, close=103.0, volume=10000.0)
        assert bar.close == 103.0
        assert bar.volume == 10000.0

    def test_bar_immutable(self):
        bar = Bar(date=datetime(2024, 1, 1), open=100.0, high=105.0, low=99.0, close=103.0, volume=10000.0)
        with pytest.raises(AttributeError):
            bar.close = 104.0

    def test_bar_from_series(self, sample_df):
        row = sample_df.iloc[0]
        bar = Bar.from_series(row)
        assert bar.open == 100.0
        assert bar.close == 101.0
        assert isinstance(bar.date, datetime)


class TestSignal:
    """Tests for Signal dataclass."""

    def test_signal_creation(self):
        signal = Signal(message="Test signal", severity="warning")
        assert signal.message == "Test signal"
        assert signal.severity == "warning"
        assert signal.timestamp is None
        assert signal.metadata is None

    def test_signal_with_metadata(self):
        signal = Signal(
            message="Price below MA",
            severity="action",
            timestamp=datetime(2024, 1, 1),
            metadata={"close": 100.0, "ma": 105.0},
        )
        assert signal.metadata["close"] == 100.0


class TestPriceHistory:
    """Tests for PriceHistory wrapper."""

    # ===== Initialization Tests =====

    def test_init_valid_df(self, sample_df):
        history = PriceHistory(sample_df)
        assert len(history) == 10

    def test_init_empty_df(self):
        empty_df = pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
        with pytest.raises(ValueError, match="empty DataFrame"):
            PriceHistory(empty_df)

    def test_init_missing_columns(self):
        df = pd.DataFrame({"date": [datetime(2024, 1, 1)], "close": [100]})
        with pytest.raises(ValueError, match="Missing required columns"):
            PriceHistory(df)

    def test_init_sorts_by_date(self):
        df = pd.DataFrame(
            {
                "date": pd.to_datetime(["2024-01-03", "2024-01-01", "2024-01-02"]),
                "open": [102.0, 100.0, 101.0],
                "high": [103.0, 101.0, 102.0],
                "low": [101.0, 99.0, 100.0],
                "close": [102.5, 100.5, 101.5],
                "volume": [1000.0, 1000.0, 1000.0],
            }
        )
        history = PriceHistory(df)
        assert history.start_date.date() == datetime(2024, 1, 1).date()
        assert history.end_date.date() == datetime(2024, 1, 3).date()

    # ===== Index-based Access Tests =====

    def test_current_bar(self, sample_df):
        history = PriceHistory(sample_df)
        bar = history.current
        assert bar.close == 110.0
        assert bar.date.date() == datetime(2024, 1, 10).date()

    def test_bar_at_positive_index(self, sample_df):
        history = PriceHistory(sample_df)
        bar = history.bar_at(0)
        assert bar.close == 101.0
        bar = history.bar_at(5)
        assert bar.close == 106.0

    def test_bar_at_negative_index(self, sample_df):
        history = PriceHistory(sample_df)
        bar = history.bar_at(-1)
        assert bar.close == 110.0
        bar = history.bar_at(-2)
        assert bar.close == 109.0

    def test_bar_at_out_of_range(self, sample_df):
        history = PriceHistory(sample_df)
        with pytest.raises(IndexError, match="out of range"):
            history.bar_at(100)

    # ===== Date-based Access Tests =====

    def test_on_valid_date(self, sample_df):
        history = PriceHistory(sample_df)
        bar = history.on("2024-01-05")
        assert bar.close == 105.0

    def test_on_invalid_date(self, sample_df):
        history = PriceHistory(sample_df)
        with pytest.raises(KeyError, match="not found in history"):
            history.on("2025-01-01")

    def test_on_with_datetime(self, sample_df):
        history = PriceHistory(sample_df)
        bar = history.on(datetime(2024, 1, 5))
        assert bar.close == 105.0

    def test_on_with_timestamp(self, sample_df):
        history = PriceHistory(sample_df)
        bar = history.on(pd.Timestamp("2024-01-05"))
        assert bar.close == 105.0

    def test_asof_exact_date(self, sample_df):
        history = PriceHistory(sample_df)
        bar = history.asof("2024-01-05")
        assert bar.close == 105.0

    def test_asof_future_date(self, sample_df):
        history = PriceHistory(sample_df)
        bar = history.asof("2024-01-15")
        assert bar.close == 110.0

    def test_asof_before_start(self, sample_df):
        history = PriceHistory(sample_df)
        with pytest.raises(ValueError, match="before earliest data"):
            history.asof("2023-12-01")

    def test_has_date_true(self, sample_df):
        history = PriceHistory(sample_df)
        assert history.has_date("2024-01-05") is True

    def test_has_date_false(self, sample_df):
        history = PriceHistory(sample_df)
        assert history.has_date("2025-01-01") is False

    def test_between_inclusive_both(self, sample_df):
        history = PriceHistory(sample_df)
        df = history.between("2024-01-03", "2024-01-07", inclusive="both")
        assert len(df) == 5
        assert df.iloc[0]["close"] == 103.0
        assert df.iloc[-1]["close"] == 107.0

    def test_between_inclusive_left(self, sample_df):
        history = PriceHistory(sample_df)
        df = history.between("2024-01-03", "2024-01-07", inclusive="left")
        assert len(df) == 4
        assert df.iloc[0]["close"] == 103.0
        assert df.iloc[-1]["close"] == 106.0

    def test_between_inclusive_right(self, sample_df):
        history = PriceHistory(sample_df)
        df = history.between("2024-01-03", "2024-01-07", inclusive="right")
        assert len(df) == 4
        assert df.iloc[0]["close"] == 104.0
        assert df.iloc[-1]["close"] == 107.0

    def test_between_inclusive_neither(self, sample_df):
        history = PriceHistory(sample_df)
        df = history.between("2024-01-03", "2024-01-07", inclusive="neither")
        assert len(df) == 3
        assert df.iloc[0]["close"] == 104.0
        assert df.iloc[-1]["close"] == 106.0

    # ===== Indicator Access Tests =====

    def test_indicator_by_index(self, sample_df_with_indicators):
        history = PriceHistory(sample_df_with_indicators)
        ma250 = history.indicator("MA250")
        assert ma250 == 95.0

    def test_indicator_by_date(self, sample_df_with_indicators):
        history = PriceHistory(sample_df_with_indicators)
        ma250 = history.indicator("MA250", date="2024-01-05")
        assert ma250 == 95.0

    def test_indicator_missing(self, sample_df):
        history = PriceHistory(sample_df)
        result = history.indicator("MA250")
        assert result is None

    def test_indicator_nan_value(self, sample_df_with_indicators):
        history = PriceHistory(sample_df_with_indicators)
        ma5_first = history.indicator("MA5", index=0)
        assert ma5_first is None

    def test_indicator_both_index_and_date_raises(self, sample_df_with_indicators):
        history = PriceHistory(sample_df_with_indicators)
        with pytest.raises(ValueError, match="Specify only one of"):
            history.indicator("MA250", index=0, date="2024-01-05")

        with pytest.raises(ValueError, match="Specify only one of"):
            history.indicator("MA250", index=0, offset=1)

        with pytest.raises(ValueError, match="Specify only one of"):
            history.indicator("MA250", date="2024-01-01", offset=1)

    def test_has_indicator_true(self, sample_df_with_indicators):
        history = PriceHistory(sample_df_with_indicators)
        assert history.has_indicator("MA250") is True

    def test_has_indicator_false(self, sample_df):
        history = PriceHistory(sample_df)
        assert history.has_indicator("MA250") is False

    # ===== Pattern Detection Tests =====

    def test_is_above_true(self, sample_df_with_indicators):
        history = PriceHistory(sample_df_with_indicators)
        assert history.is_above("MA250", bars=1) is True

    def test_is_above_false(self):
        df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=5),
                "open": [100.0, 99.0, 98.0, 97.0, 96.0],
                "high": [101.0, 100.0, 99.0, 98.0, 97.0],
                "low": [99.0, 98.0, 97.0, 96.0, 95.0],
                "close": [100.0, 99.0, 98.0, 97.0, 96.0],
                "volume": [1000.0] * 5,
                "MA250": [105.0] * 5,
            }
        )
        history = PriceHistory(df)
        assert history.is_above("MA250", bars=1) is False

    def test_is_below_true(self):
        df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=5),
                "open": [100.0, 99.0, 98.0, 97.0, 96.0],
                "high": [101.0, 100.0, 99.0, 98.0, 97.0],
                "low": [99.0, 98.0, 97.0, 96.0, 95.0],
                "close": [100.0, 99.0, 98.0, 97.0, 96.0],
                "volume": [1000.0] * 5,
                "MA250": [105.0] * 5,
            }
        )
        history = PriceHistory(df)
        assert history.is_below("MA250", bars=1) is True

    def test_crossed_above_true(self):
        df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=5),
                "open": [100.0, 101.0, 102.0, 103.0, 104.0],
                "high": [101.0, 102.0, 103.0, 104.0, 105.0],
                "low": [99.0, 100.0, 101.0, 102.0, 103.0],
                "close": [100.0, 101.0, 102.0, 103.0, 104.0],
                "volume": [1000.0] * 5,
                "MA60": [101.5, 101.5, 101.5, 101.5, 101.5],
            }
        )
        history = PriceHistory(df)
        # At index 3: close=103 > MA60=101.5, at index 2: close=102 > MA60=101.5
        # Need to check within_bars=3 to see the cross from index 1 (101 < 101.5) to index 2 (102 > 101.5)
        assert history.crossed_above("MA60", within_bars=3) is True

    def test_crossed_below_true(self):
        df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=5),
                "open": [104.0, 103.0, 102.0, 101.0, 100.0],
                "high": [105.0, 104.0, 103.0, 102.0, 101.0],
                "low": [103.0, 102.0, 101.0, 100.0, 99.0],
                "close": [104.0, 103.0, 102.0, 101.0, 100.0],
                "volume": [1000.0] * 5,
                "MA60": [102.5, 102.5, 102.5, 102.5, 102.5],
            }
        )
        history = PriceHistory(df)
        # At index 3: close=101 < MA60=102.5, at index 2: close=102 < MA60=102.5
        # Need to check within_bars=3 to see the cross from index 1 (103 > 102.5) to index 2 (102 < 102.5)
        assert history.crossed_below("MA60", within_bars=3) is True

    # ===== History Access Tests =====

    def test_history_close(self, sample_df):
        history = PriceHistory(sample_df)
        closes = history.history(3, "close")
        assert len(closes) == 3
        assert closes.iloc[-1] == 110.0

    def test_history_invalid_field(self, sample_df):
        history = PriceHistory(sample_df)
        with pytest.raises(KeyError, match="not found"):
            history.history(3, "invalid_field")

    # ===== DataFrame Access Tests =====

    def test_df_returns_copy(self, sample_df):
        history = PriceHistory(sample_df)
        df = history.df
        df.iloc[0, df.columns.get_loc("close")] = 999
        assert history.current.close != 999

    def test_tail(self, sample_df):
        history = PriceHistory(sample_df)
        df = history.tail(3)
        assert len(df) == 3
        assert df.iloc[-1]["close"] == 110.0

    # ===== Metadata Tests =====

    def test_len(self, sample_df):
        history = PriceHistory(sample_df)
        assert len(history) == 10

    def test_columns(self, sample_df_with_indicators):
        history = PriceHistory(sample_df_with_indicators)
        columns = history.columns
        assert "close" in columns
        assert "MA250" in columns

    def test_start_date(self, sample_df):
        history = PriceHistory(sample_df)
        assert history.start_date.date() == datetime(2024, 1, 1).date()

    def test_end_date(self, sample_df):
        history = PriceHistory(sample_df)
        assert history.end_date.date() == datetime(2024, 1, 10).date()

    def test_date_range(self, sample_df):
        history = PriceHistory(sample_df)
        start, end = history.date_range
        assert start.date() == datetime(2024, 1, 1).date()
        assert end.date() == datetime(2024, 1, 10).date()

    def test_repr(self, sample_df):
        history = PriceHistory(sample_df)
        repr_str = repr(history)
        assert "PriceHistory" in repr_str
        assert "10 bars" in repr_str
        assert "2024-01-01" in repr_str
        assert "2024-01-10" in repr_str
