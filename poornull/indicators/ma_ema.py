"""
Moving Average (MA) and Exponential Moving Average (EMA) indicators.

This module provides functions to calculate MA and EMA for different periods.
"""

import pandas as pd

from poornull.data.models import PriceHistory


def calculate_ma(
    df: pd.DataFrame,
    close_col: str = "close",
    periods: list[int] | None = None,
) -> pd.DataFrame:
    """
    Calculate Simple Moving Average (MA) for specified periods.

    Args:
        df: DataFrame with price data. Must have a date/timestamp column and close prices.
        close_col: Column name for closing prices (default "close")
        periods: List of periods for MA calculation (default: [5, 10, 20, 30, 60])

    Returns:
        DataFrame with added MA columns (MA5, MA10, MA20, etc.)

    Example:
        >>> import pandas as pd
        >>> dates = pd.date_range("2024-01-01", periods=100, freq="D")
        >>> prices = [100 + i * 0.5 for i in range(100)]
        >>> df = pd.DataFrame({"date": dates, "close": prices})
        >>> df = calculate_ma(df, close_col="close", periods=[5, 10, 20])
        >>> print(df[["date", "close", "MA5", "MA10", "MA20"]].tail())
    """
    if periods is None:
        periods = [5, 10, 20, 30, 60]

    df = df.copy()

    # Sort by date to ensure proper calculation order
    date_col = None
    for col in df.columns:
        col_lower = str(col).lower()
        if "date" in col_lower or "timestamp" in col_lower or "日期" in str(col):
            date_col = col
            break

    if date_col:
        df = df.sort_values(by=date_col)
    else:
        # If no date column found, sort by first column as fallback
        df = df.sort_values(by=df.columns[0])

    # Validate close column exists
    if close_col not in df.columns:
        raise ValueError(f"Close column '{close_col}' not found in DataFrame. Available columns: {list(df.columns)}")

    # Calculate MA for each period
    for period in periods:
        df[f"MA{period}"] = df[close_col].rolling(window=period, min_periods=1).mean()

    return df


def calculate_ema(
    df: pd.DataFrame,
    close_col: str = "close",
    periods: list[int] | None = None,
    adjust: bool = False,
) -> pd.DataFrame:
    """
    Calculate Exponential Moving Average (EMA) for specified periods.

    Args:
        df: DataFrame with price data. Must have a date/timestamp column and close prices.
        close_col: Column name for closing prices (default "close")
        periods: List of periods for EMA calculation (default: [5, 10, 20, 30, 60])
        adjust: Whether to use adjusted EMA calculation (default: False, matches standard EMA)

    Returns:
        DataFrame with added EMA columns (EMA5, EMA10, EMA20, etc.)

    Example:
        >>> import pandas as pd
        >>> dates = pd.date_range("2024-01-01", periods=100, freq="D")
        >>> prices = [100 + i * 0.5 for i in range(100)]
        >>> df = pd.DataFrame({"date": dates, "close": prices})
        >>> df = calculate_ema(df, close_col="close", periods=[5, 10, 20])
        >>> print(df[["date", "close", "EMA5", "EMA10", "EMA20"]].tail())
    """
    if periods is None:
        periods = [5, 10, 20, 30, 60]

    df = df.copy()

    # Sort by date to ensure proper calculation order
    date_col = None
    for col in df.columns:
        col_lower = str(col).lower()
        if "date" in col_lower or "timestamp" in col_lower or "日期" in str(col):
            date_col = col
            break

    if date_col:
        df = df.sort_values(by=date_col)
    else:
        # If no date column found, sort by first column as fallback
        df = df.sort_values(by=df.columns[0])

    # Validate close column exists
    if close_col not in df.columns:
        raise ValueError(f"Close column '{close_col}' not found in DataFrame. Available columns: {list(df.columns)}")

    # Calculate EMA for each period
    for period in periods:
        df[f"EMA{period}"] = df[close_col].ewm(span=period, adjust=adjust).mean()

    return df


def calculate_ma_ema(
    df: pd.DataFrame,
    close_col: str = "close",
    ma_periods: list[int] | None = None,
    ema_periods: list[int] | None = None,
    ema_adjust: bool = False,
) -> pd.DataFrame:
    """
    Calculate both MA and EMA for specified periods.

    Args:
        df: DataFrame with price data. Must have a date/timestamp column and close prices.
        close_col: Column name for closing prices (default "close")
        ma_periods: List of periods for MA calculation (default: [5, 10, 20, 30, 60])
        ema_periods: List of periods for EMA calculation (default: [5, 10, 20, 30, 60])
        ema_adjust: Whether to use adjusted EMA calculation (default: False)

    Returns:
        DataFrame with added MA and EMA columns

    Example:
        >>> import pandas as pd
        >>> dates = pd.date_range("2024-01-01", periods=100, freq="D")
        >>> prices = [100 + i * 0.5 for i in range(100)]
        >>> df = pd.DataFrame({"date": dates, "close": prices})
        >>> df = calculate_ma_ema(df, close_col="close", ma_periods=[5, 10], ema_periods=[5, 10])
        >>> print(df[["date", "close", "MA5", "MA10", "EMA5", "EMA10"]].tail())
    """
    df = calculate_ma(df, close_col=close_col, periods=ma_periods)
    df = calculate_ema(df, close_col=close_col, periods=ema_periods, adjust=ema_adjust)
    return df


# ===== PriceHistory API =====


def with_ma(
    history: PriceHistory,
    periods: list[int] | None = None,
) -> PriceHistory:
    """
    Add Moving Average (MA) indicators to PriceHistory.

    Args:
        history: PriceHistory object with price data
        periods: List of periods for MA calculation (default: [5, 10, 20, 30, 60])

    Returns:
        New PriceHistory with MA columns added (MA5, MA10, MA20, etc.)

    Example:
        >>> from poornull.data import PriceHistory
        >>> from poornull.data import download_daily
        >>> df = download_daily("600036", "20240101", "20241231")
        >>> history = PriceHistory(df)
        >>> history = with_ma(history, periods=[5, 10, 20, 30, 60, 250])
        >>> print(f"Has MA250: {history.has_indicator('MA250')}")
    """
    if periods is None:
        periods = [5, 10, 20, 30, 60]

    df = history.df

    for period in periods:
        df[f"MA{period}"] = df["close"].rolling(window=period, min_periods=1).mean()

    return PriceHistory(df)


def with_ema(
    history: PriceHistory,
    periods: list[int] | None = None,
    adjust: bool = False,
) -> PriceHistory:
    """
    Add Exponential Moving Average (EMA) indicators to PriceHistory.

    Args:
        history: PriceHistory object with price data
        periods: List of periods for EMA calculation (default: [5, 10, 20, 30, 60])
        adjust: Whether to use adjusted EMA calculation (default: False)

    Returns:
        New PriceHistory with EMA columns added (EMA5, EMA10, EMA20, etc.)

    Example:
        >>> history = with_ema(history, periods=[12, 26])
        >>> print(f"Has EMA12: {history.has_indicator('EMA12')}")
    """
    if periods is None:
        periods = [5, 10, 20, 30, 60]

    df = history.df

    for period in periods:
        df[f"EMA{period}"] = df["close"].ewm(span=period, adjust=adjust).mean()

    return PriceHistory(df)


def with_ma_ema(
    history: PriceHistory,
    ma_periods: list[int] | None = None,
    ema_periods: list[int] | None = None,
    ema_adjust: bool = False,
) -> PriceHistory:
    """
    Add both MA and EMA indicators to PriceHistory.

    Args:
        history: PriceHistory object with price data
        ma_periods: List of periods for MA calculation (default: [5, 10, 20, 30, 60])
        ema_periods: List of periods for EMA calculation (default: [5, 10, 20, 30, 60])
        ema_adjust: Whether to use adjusted EMA calculation (default: False)

    Returns:
        New PriceHistory with MA and EMA columns added

    Example:
        >>> history = PriceHistory(df)
        >>> history = with_ma_ema(history, ma_periods=[5, 10, 20], ema_periods=[12, 26])
        >>> # Or chain them:
        >>> history = with_ma(history, [5, 10, 20, 30, 60, 250])
        >>> history = with_ema(history, [12, 26])
    """
    history = with_ma(history, periods=ma_periods)
    history = with_ema(history, periods=ema_periods, adjust=ema_adjust)
    return history
