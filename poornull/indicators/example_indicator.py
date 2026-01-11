"""
Example indicator template.

This file shows the pattern for creating new indicators.
Copy this structure when creating new indicators.
"""

import pandas as pd


def calculate_example_indicator(
    df: pd.DataFrame,
    close_col: str = "close",
    period: int = 14,
    **kwargs,
) -> pd.DataFrame:
    """
    Calculate example indicator.

    This is a template showing the standard pattern for indicator functions.

    Args:
        df: DataFrame with price data. Must have a date/timestamp column and close prices.
        close_col: Column name for closing prices (default "close")
        period: Period for calculation (default 14)
        **kwargs: Additional parameters for the indicator

    Returns:
        DataFrame with added indicator column(s)

    Example:
        >>> import pandas as pd
        >>> dates = pd.date_range("2024-01-01", periods=50, freq="D")
        >>> prices = [100 + i * 0.5 for i in range(50)]
        >>> df = pd.DataFrame({"date": dates, "close": prices})
        >>> df = calculate_example_indicator(df, close_col="close", period=14)
        >>> print(df[["date", "close", "INDICATOR"]].tail())
    """
    df = df.copy()

    # Step 1: Sort by date to ensure proper calculation order
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

    # Step 2: Validate required columns exist
    if close_col not in df.columns:
        raise ValueError(f"Close column '{close_col}' not found in DataFrame. Available columns: {list(df.columns)}")

    # Step 3: Calculate the indicator
    # Replace this with your actual indicator calculation
    df["INDICATOR"] = df[close_col].rolling(window=period).mean()  # Example calculation

    return df
