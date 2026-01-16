"""
Tonghuashun (同花顺) compatible MACD calculation.

This module provides MACD calculation that matches Tonghuashun's values:
- Uses standard EMA calculation (adjust=False)
- Uses 2x multiplier for histogram (MACD bar) by default
- Returns columns named DIF, DEA, MACD (matching Tonghuashun terminology)
"""

import logging

import pandas as pd

from poornull.data.models import PriceHistory

logger = logging.getLogger(__name__)


def tonghuashun_macd(
    df: pd.DataFrame,
    close_col: str = "close",
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    histogram_multiplier: float = 2.0,
) -> pd.DataFrame:
    """
    Calculate MACD exactly as Tonghuashun does.

    This is a pure indicator function that takes price data and returns MACD values.
    It matches Tonghuashun's calculation:
    - Uses standard EMA (adjust=False)
    - Applies 2x multiplier to histogram by default (Tonghuashun's MACD bar)
    - Returns columns named DIF, DEA, MACD (matching Tonghuashun terminology)

    Args:
        df: DataFrame with price data. Must have a date/timestamp column and close prices.
        close_col: Column name for closing prices (default "close")
        fast: Fast EMA period (default 12)
        slow: Slow EMA period (default 26)
        signal: Signal line EMA period (default 9)
        histogram_multiplier: Multiplier for histogram (default 2.0 for Tonghuashun)

    Returns:
        DataFrame with added columns:
        - DIF: Fast EMA - Slow EMA (差离值)
        - DEA: Signal line, EMA of DIF (讯号线)
        - MACD: Histogram with multiplier applied (柱状图)

    Example:
        >>> import akshare as ak
        >>> df = ak.stock_zh_a_hist("600036", period="daily", start_date="20240101", end_date="20241231", adjust="")
        >>> df = df.rename(columns={'收盘': 'close', '日期': 'date'})
        >>> df = tonghuashun_macd(df, close_col='close')
        >>> print(df[['date', 'close', 'DIF', 'DEA', 'MACD']].tail())
    """
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

    # Calculate EMAs using standard method (adjust=False)
    ema_fast = df[close_col].ewm(span=fast, adjust=False).mean()
    ema_slow = df[close_col].ewm(span=slow, adjust=False).mean()

    # MACD line (DIF) = Fast EMA - Slow EMA
    df["DIF"] = ema_fast - ema_slow

    # Signal line (DEA) = EMA of DIF
    df["DEA"] = df["DIF"].ewm(span=signal, adjust=False).mean()

    # Histogram (MACD) = (DIF - DEA) × multiplier
    # Note: Tonghuashun uses 2x multiplier for the histogram display
    df["MACD"] = (df["DIF"] - df["DEA"]) * histogram_multiplier

    return df


def find_macd_crossovers(
    df: pd.DataFrame,
    dif_col: str = "DIF",
    dea_col: str = "DEA",
    date_col: str | None = None,
) -> pd.DataFrame:
    """
    Find MACD crossovers and identify their type.

    Detects when DIF (MACD line) crosses DEA (Signal line):
    - Golden Cross (Bullish): DIF crosses above DEA
    - Death Cross (Bearish): DIF crosses below DEA

    Args:
        df: DataFrame with MACD data (must have DIF and DEA columns)
        dif_col: Column name for DIF (default "DIF")
        dea_col: Column name for DEA (default "DEA")
        date_col: Column name for dates (auto-detected if None)

    Returns:
        DataFrame with crossover information:
        - date: Date of crossover
        - type: "golden" or "death"
        - dif: DIF value at crossover
        - dea: DEA value at crossover
        - macd: MACD histogram value at crossover
        - close_price: Closing price at crossover (if available)

    Example:
        >>> df = tonghuashun_macd(price_data)
        >>> crossovers = find_macd_crossovers(df)
        >>> print(crossovers[['date', 'type', 'dif', 'dea']])
    """
    df = df.copy()

    # Validate required columns
    if dif_col not in df.columns:
        raise ValueError(f"DIF column '{dif_col}' not found. Available columns: {list(df.columns)}")
    if dea_col not in df.columns:
        raise ValueError(f"DEA column '{dea_col}' not found. Available columns: {list(df.columns)}")

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
    # Golden cross: DIF was below/equal DEA, now above
    # Death cross: DIF was above/equal DEA, now below
    df["prev_DIF"] = df[dif_col].shift(1)
    df["prev_DEA"] = df[dea_col].shift(1)

    # Golden cross: DIF crosses above DEA
    golden_cross = (df[dif_col] > df[dea_col]) & (df["prev_DIF"] <= df["prev_DEA"])

    # Death cross: DIF crosses below DEA
    death_cross = (df[dif_col] < df[dea_col]) & (df["prev_DIF"] >= df["prev_DEA"])

    # Combine crossovers
    df["crossover"] = golden_cross | death_cross
    df["crossover_type"] = "none"
    df.loc[golden_cross, "crossover_type"] = "golden"
    df.loc[death_cross, "crossover_type"] = "death"

    # Extract crossover information
    crossovers = df[df["crossover"]].copy()
    if crossovers.empty:
        return pd.DataFrame(columns=["date", "type", "dif", "dea", "macd", "close_price"])

    # Get closing price column if available
    close_col = None
    for col in df.columns:
        col_lower = str(col).lower()
        if "close" in col_lower or "收盘" in str(col):
            close_col = col
            break

    # Build result DataFrame
    result_data = {
        "date": crossovers[date_col],
        "type": crossovers["crossover_type"],
        "dif": crossovers[dif_col],
        "dea": crossovers[dea_col],
    }

    # Add MACD histogram if available
    if "MACD" in df.columns:
        result_data["macd"] = crossovers["MACD"]
    elif "macd" in df.columns:
        result_data["macd"] = crossovers["macd"]

    # Add closing price if available
    if close_col:
        result_data["close_price"] = crossovers[close_col]

    result = pd.DataFrame(result_data)

    # Clean up temporary columns
    df.drop(columns=["prev_DIF", "prev_DEA", "crossover", "crossover_type"], errors="ignore")

    return result


def calculate_tonghuashun_macd(
    stock_code: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """
    Convenience function: Fetch data and calculate Tonghuashun MACD.

    This is a convenience wrapper that fetches UNADJUSTED data and calculates MACD.
    For reusable indicator calculation, use tonghuashun_macd() directly.

    Args:
        stock_code: Stock code (e.g., "600036")
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format

    Returns:
        DataFrame with price data and MACD columns (DIF, DEA, MACD)

    Note:
        This function fetches UNADJUSTED prices (不复权) as Tonghuashun uses for MACD.
    """
    import akshare as ak

    # Fetch UNADJUSTED data (this is what Tonghuashun uses for MACD calculation)
    df = ak.stock_zh_a_hist(
        symbol=stock_code,
        period="daily",
        start_date=start_date,
        end_date=end_date,
        adjust="",  # UNADJUSTED - KEY for matching Tonghuashun!
    )

    if df.empty:
        raise ValueError(f"No data found for stock {stock_code}")

    # Convert column names to English
    column_mapping = {
        "日期": "date",
        "收盘": "close",
        "开盘": "open",
        "最高": "high",
        "最低": "low",
        "成交量": "volume",
    }
    df = df.rename(columns=column_mapping)
    df["date"] = pd.to_datetime(df["date"])

    # Use the pure indicator function
    df = tonghuashun_macd(df, close_col="close")

    return df


def main():
    """Quick test/debug function for Tonghuashun MACD calculation."""
    from datetime import datetime, timedelta

    import akshare as ak

    # Test with stock 600036
    stock_code = "600036"
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # ~2 years for proper warm-up

    logger.info("=" * 80)
    logger.info("Tonghuashun MACD Calculation Test")
    logger.info("=" * 80)
    logger.info(f"Stock: {stock_code}")
    logger.info(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    logger.info("Using: UNADJUSTED prices (不复权) - as Tonghuashun does")

    try:
        # Fetch data
        logger.info("Fetching data...")
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d"),
            adjust="",  # UNADJUSTED
        )

        if df.empty:
            logger.error(f"No data found for stock {stock_code}")
            return

        # Convert column names
        column_mapping = {
            "日期": "date",
            "收盘": "close",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
        }
        df = df.rename(columns=column_mapping)
        df["date"] = pd.to_datetime(df["date"])

        logger.info(f"Fetched {len(df)} records")
        logger.info(f"   Date range: {df['date'].min()} to {df['date'].max()}")

        # Calculate MACD using the indicator function
        logger.info("Calculating MACD (Tonghuashun settings)...")
        logger.info("   - Fast EMA: 12")
        logger.info("   - Slow EMA: 26")
        logger.info("   - Signal EMA: 9")
        logger.info("   - Histogram multiplier: 2.0")

        df = tonghuashun_macd(df, close_col="close", fast=12, slow=26, signal=9, histogram_multiplier=2.0)

        # Show last 10 days
        logger.info("=" * 80)
        logger.info(f"MACD VALUES FOR STOCK {stock_code} (Last 10 days)")
        logger.info("=" * 80)
        logger.info("\nDate       | Close  |   DIF   |   DEA   |  MACD")
        logger.info("-" * 60)

        for _, row in df.tail(10).iterrows():
            date_str = row["date"].strftime("%Y-%m-%d")
            logger.info(
                f"{date_str} | {row['close']:6.2f} | {row['DIF']:7.4f} | {row['DEA']:7.4f} | {row['MACD']:6.4f}"
            )

        logger.info("\n" + "=" * 80)
        logger.info("Calculation complete!")
        logger.info("=" * 80)
        logger.info("KEY POINTS:")
        logger.info("   1. Tonghuashun uses UNADJUSTED (不复权) prices for MACD calculation")
        logger.info("   2. Tonghuashun uses 2x multiplier for MACD histogram display")
        logger.info("   3. DIF = Fast EMA - Slow EMA")
        logger.info("   4. DEA = Signal line (EMA of DIF)")
        logger.info("   5. MACD = (DIF - DEA) × 2  ← Note the 2x multiplier!")
        logger.info("=" * 80)

        return df

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return None


# ===== PriceHistory API =====


def with_macd(
    history: PriceHistory,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
    histogram_multiplier: float = 2.0,
) -> PriceHistory:
    """
    Add MACD indicators to PriceHistory (Tonghuashun-compatible).

    Args:
        history: PriceHistory object with price data
        fast: Fast EMA period (default 12)
        slow: Slow EMA period (default 26)
        signal: Signal line EMA period (default 9)
        histogram_multiplier: Multiplier for histogram (default 2.0 for Tonghuashun)

    Returns:
        New PriceHistory with MACD columns added:
        - DIF: Fast EMA - Slow EMA (MACD line)
        - DEA: Signal line, EMA of DIF
        - MACD: Histogram with multiplier applied

    Example:
        >>> from poornull.data import PriceHistory
        >>> from poornull.data import download_daily
        >>> df = download_daily("600036", "20240101", "20241231")
        >>> history = PriceHistory(df)
        >>> history = with_macd(history)
        >>> print(f"Has MACD: {history.has_indicator('MACD')}")
    """
    df = history.df

    # Calculate EMAs
    ema_fast = df["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = df["close"].ewm(span=slow, adjust=False).mean()

    # MACD line (DIF)
    df["DIF"] = ema_fast - ema_slow

    # Signal line (DEA)
    df["DEA"] = df["DIF"].ewm(span=signal, adjust=False).mean()

    # Histogram (MACD)
    df["MACD"] = (df["DIF"] - df["DEA"]) * histogram_multiplier

    return PriceHistory(df)


if __name__ == "__main__":
    main()
