"""
Weekly MA crossover indicator.

This module provides functions to calculate weekly MA values and detect crossovers
between MA20/MA30 and MA60.
"""

import pandas as pd


def calculate_weekly_ma(
    df: pd.DataFrame,
    close_col: str = "close",
    periods: list[int] | None = None,
) -> pd.DataFrame:
    """
    Calculate weekly MA values for specified periods.

    Args:
        df: DataFrame with weekly price data. Must have a date/timestamp column and close prices.
        close_col: Column name for closing prices (default "close")
        periods: List of periods for MA calculation (default: [20, 30, 60, 120, 250])

    Returns:
        DataFrame with added MA columns (MA20, MA30, MA60, MA120, MA250)

    Example:
        >>> from poornull.data import download_weekly
        >>> df = download_weekly("600036", "20200101", "20241231")
        >>> df = calculate_weekly_ma(df)
        >>> print(df[["date", "close", "MA20", "MA30", "MA60"]].tail())
    """
    if periods is None:
        periods = [20, 30, 60, 120, 250]

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


def find_ma_crossovers(
    df: pd.DataFrame,
    ma20_col: str = "MA20",
    ma30_col: str = "MA30",
    ma60_col: str = "MA60",
    date_col: str | None = None,
) -> pd.DataFrame:
    """
    Find crossovers between MA20/MA30 and MA60.

    Detects when MA20 or MA30 crosses above or below MA60:
    - Golden Cross (Bullish): MA20/MA30 crosses above MA60
    - Death Cross (Bearish): MA20/MA30 crosses below MA60

    Args:
        df: DataFrame with MA columns
        ma20_col: Column name for MA20 (default "MA20")
        ma30_col: Column name for MA30 (default "MA30")
        ma60_col: Column name for MA60 (default "MA60")
        date_col: Column name for dates (auto-detected if None)

    Returns:
        DataFrame with crossover information:
        - date: Date of crossover
        - type: "golden_ma20", "death_ma20", "golden_ma30", "death_ma30"
        - ma20: MA20 value at crossover
        - ma30: MA30 value at crossover
        - ma60: MA60 value at crossover
        - close_price: Closing price at crossover (if available)

    Example:
        >>> from poornull.data import download_weekly
        >>> df = download_weekly("600036", "20200101", "20241231")
        >>> df = calculate_weekly_ma(df)
        >>> crossovers = find_ma_crossovers(df)
        >>> print(crossovers)
    """
    df = df.copy()

    # Validate required columns
    if ma20_col not in df.columns:
        raise ValueError(f"MA20 column '{ma20_col}' not found. Available columns: {list(df.columns)}")
    if ma30_col not in df.columns:
        raise ValueError(f"MA30 column '{ma30_col}' not found. Available columns: {list(df.columns)}")
    if ma60_col not in df.columns:
        raise ValueError(f"MA60 column '{ma60_col}' not found. Available columns: {list(df.columns)}")

    # Auto-detect date column if not provided
    if date_col is None:
        for col in df.columns:
            col_lower = str(col).lower()
            if "date" in col_lower or "timestamp" in col_lower or "时间" in str(col):
                date_col = col
                break

    if date_col is None:
        date_col = df.columns[0]  # Use first column as fallback

    # Sort by date to ensure proper order
    if date_col in df.columns:
        df = df.sort_values(by=date_col)

    # Detect crossovers
    # Previous values for comparison
    df["prev_MA20"] = df[ma20_col].shift(1)
    df["prev_MA30"] = df[ma30_col].shift(1)
    df["prev_MA60"] = df[ma60_col].shift(1)

    # MA20 crossovers
    # Golden cross: MA20 was below/equal MA60, now above
    ma20_golden = (df[ma20_col] > df[ma60_col]) & (df["prev_MA20"] <= df["prev_MA60"])
    # Death cross: MA20 was above/equal MA60, now below
    ma20_death = (df[ma20_col] < df[ma60_col]) & (df["prev_MA20"] >= df["prev_MA60"])

    # MA30 crossovers
    # Golden cross: MA30 was below/equal MA60, now above
    ma30_golden = (df[ma30_col] > df[ma60_col]) & (df["prev_MA30"] <= df["prev_MA60"])
    # Death cross: MA30 was above/equal MA60, now below
    ma30_death = (df[ma30_col] < df[ma60_col]) & (df["prev_MA30"] >= df["prev_MA60"])

    # Combine all crossovers
    crossovers_list = []

    # MA20 golden crosses
    for idx in df[ma20_golden].index:
        row = df.loc[idx]
        crossovers_list.append(
            {
                "date": row[date_col],
                "type": "golden_ma20",
                "ma20": row[ma20_col],
                "ma30": row[ma30_col],
                "ma60": row[ma60_col],
                "close_price": row.get("close", None),
            }
        )

    # MA20 death crosses
    for idx in df[ma20_death].index:
        row = df.loc[idx]
        crossovers_list.append(
            {
                "date": row[date_col],
                "type": "death_ma20",
                "ma20": row[ma20_col],
                "ma30": row[ma30_col],
                "ma60": row[ma60_col],
                "close_price": row.get("close", None),
            }
        )

    # MA30 golden crosses
    for idx in df[ma30_golden].index:
        row = df.loc[idx]
        crossovers_list.append(
            {
                "date": row[date_col],
                "type": "golden_ma30",
                "ma20": row[ma20_col],
                "ma30": row[ma30_col],
                "ma60": row[ma60_col],
                "close_price": row.get("close", None),
            }
        )

    # MA30 death crosses
    for idx in df[ma30_death].index:
        row = df.loc[idx]
        crossovers_list.append(
            {
                "date": row[date_col],
                "type": "death_ma30",
                "ma20": row[ma20_col],
                "ma30": row[ma30_col],
                "ma60": row[ma60_col],
                "close_price": row.get("close", None),
            }
        )

    if not crossovers_list:
        return pd.DataFrame(columns=["date", "type", "ma20", "ma30", "ma60", "close_price"])

    result = pd.DataFrame(crossovers_list)
    result = result.sort_values(by="date")

    return result


def find_ma_above_ma60(
    df: pd.DataFrame,
    ma20_col: str = "MA20",
    ma30_col: str = "MA30",
    ma60_col: str = "MA60",
    date_col: str | None = None,
) -> pd.DataFrame:
    """
    Find periods where MA20 or MA30 is above MA60 (beats MA60).

    Args:
        df: DataFrame with MA columns
        ma20_col: Column name for MA20 (default "MA20")
        ma30_col: Column name for MA30 (default "MA30")
        ma60_col: Column name for MA60 (default "MA60")
        date_col: Column name for dates (auto-detected if None)

    Returns:
        DataFrame with periods where MA20 or MA30 is above MA60:
        - date: Date
        - ma20_above: True if MA20 > MA60
        - ma30_above: True if MA30 > MA60
        - ma20: MA20 value
        - ma30: MA30 value
        - ma60: MA60 value
        - close_price: Closing price

    Example:
        >>> from poornull.data import download_weekly
        >>> df = download_weekly("600036", "20200101", "20241231")
        >>> df = calculate_weekly_ma(df)
        >>> above_periods = find_ma_above_ma60(df)
        >>> print(above_periods[above_periods["ma20_above"] | above_periods["ma30_above"]])
    """
    df = df.copy()

    # Validate required columns
    if ma20_col not in df.columns:
        raise ValueError(f"MA20 column '{ma20_col}' not found. Available columns: {list(df.columns)}")
    if ma30_col not in df.columns:
        raise ValueError(f"MA30 column '{ma30_col}' not found. Available columns: {list(df.columns)}")
    if ma60_col not in df.columns:
        raise ValueError(f"MA60 column '{ma60_col}' not found. Available columns: {list(df.columns)}")

    # Auto-detect date column if not provided
    if date_col is None:
        for col in df.columns:
            col_lower = str(col).lower()
            if "date" in col_lower or "timestamp" in col_lower or "时间" in str(col):
                date_col = col
                break

    if date_col is None:
        date_col = df.columns[0]  # Use first column as fallback

    # Sort by date
    if date_col in df.columns:
        df = df.sort_values(by=date_col)

    # Find where MA20 or MA30 is above MA60
    df["ma20_above"] = df[ma20_col] > df[ma60_col]
    df["ma30_above"] = df[ma30_col] > df[ma60_col]

    # Filter to only rows where at least one is above
    result = df[df["ma20_above"] | df["ma30_above"]].copy()

    if result.empty:
        return pd.DataFrame(columns=["date", "ma20_above", "ma30_above", "ma20", "ma30", "ma60", "close_price"])

    # Select relevant columns
    result_data = {
        "date": result[date_col],
        "ma20_above": result["ma20_above"],
        "ma30_above": result["ma30_above"],
        "ma20": result[ma20_col],
        "ma30": result[ma30_col],
        "ma60": result[ma60_col],
    }

    if "close" in result.columns:
        result_data["close_price"] = result["close"]

    return pd.DataFrame(result_data)
