"""
Tonghuashun (同花顺) compatible MACD calculation.

This module provides MACD calculation that matches Tonghuashun's values:
- Uses standard EMA calculation (adjust=False)
- Uses 2x multiplier for histogram (MACD bar) by default
- Returns columns named DIF, DEA, MACD (matching Tonghuashun terminology)
"""

import pandas as pd


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

    print("=" * 80)
    print("Tonghuashun MACD Calculation Test")
    print("=" * 80)
    print(f"\nStock: {stock_code}")
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print("Using: UNADJUSTED prices (不复权) - as Tonghuashun does")
    print()

    try:
        # Fetch data
        print("📊 Fetching data...")
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d"),
            adjust="",  # UNADJUSTED
        )

        if df.empty:
            print(f"❌ No data found for stock {stock_code}")
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

        print(f"✅ Fetched {len(df)} records")
        print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
        print()

        # Calculate MACD using the indicator function
        print("📈 Calculating MACD (Tonghuashun settings)...")
        print("   - Fast EMA: 12")
        print("   - Slow EMA: 26")
        print("   - Signal EMA: 9")
        print("   - Histogram multiplier: 2.0")
        print()

        df = tonghuashun_macd(df, close_col="close", fast=12, slow=26, signal=9, histogram_multiplier=2.0)

        # Show last 10 days
        print("=" * 80)
        print(f"📊 MACD VALUES FOR STOCK {stock_code} (Last 10 days)")
        print("=" * 80)
        print("\nDate       | Close  |   DIF   |   DEA   |  MACD")
        print("-" * 60)

        for _, row in df.tail(10).iterrows():
            date_str = row["date"].strftime("%Y-%m-%d")
            print(f"{date_str} | {row['close']:6.2f} | {row['DIF']:7.4f} | {row['DEA']:7.4f} | {row['MACD']:6.4f}")

        print("\n" + "=" * 80)
        print("✅ Calculation complete!")
        print("=" * 80)
        print("\n💡 KEY POINTS:")
        print("   1. Tonghuashun uses UNADJUSTED (不复权) prices for MACD calculation")
        print("   2. Tonghuashun uses 2x multiplier for MACD histogram display")
        print("   3. DIF = Fast EMA - Slow EMA")
        print("   4. DEA = Signal line (EMA of DIF)")
        print("   5. MACD = (DIF - DEA) × 2  ← Note the 2x multiplier!")
        print("=" * 80)

        return df

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()
