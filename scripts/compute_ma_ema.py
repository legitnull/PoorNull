"""
Script to compute or fetch MA/EMA (Moving Average/Exponential Moving Average) values.

This script can:
1. Fetch MA/EMA values from akshare if available
2. Compute MA/EMA values locally using pandas
3. Process stocks from watchlists
"""

import sys
from pathlib import Path

# Add parent directory to path to import poornull
sys.path.insert(0, str(Path(__file__).parent.parent))

import akshare as ak
import pandas as pd

from poornull.data import download_daily
from poornull.watchlists import get_watchlist


def compute_ma_ema_local(
    df: pd.DataFrame,
    close_col: str = "close",
    ma_periods: list[int] | None = None,
    ema_periods: list[int] | None = None,
) -> pd.DataFrame:
    """
    Compute MA and EMA values locally using pandas.

    Args:
        df: DataFrame with price data (must have date and close columns)
        close_col: Column name for closing prices
        ma_periods: List of MA periods to compute (default: [5, 10, 20, 30, 60])
        ema_periods: List of EMA periods to compute (default: [5, 10, 20, 30, 60])

    Returns:
        DataFrame with added MA and EMA columns
    """
    if ma_periods is None:
        ma_periods = [5, 10, 20, 30, 60]
    if ema_periods is None:
        ema_periods = [5, 10, 20, 30, 60]

    df = df.copy()

    # Ensure data is sorted by date
    if "date" in df.columns:
        df = df.sort_values(by="date")

    # Compute MA (Simple Moving Average)
    for period in ma_periods:
        df[f"MA{period}"] = df[close_col].rolling(window=period).mean()

    # Compute EMA (Exponential Moving Average)
    for period in ema_periods:
        df[f"EMA{period}"] = df[close_col].ewm(span=period, adjust=False).mean()

    return df


def fetch_ma_ema_from_akshare(
    stock_code: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame | None:
    """
    Try to fetch MA/EMA values from akshare if available.

    Args:
        stock_code: Stock code (e.g., "600036")
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format

    Returns:
        DataFrame with MA/EMA columns if available, None otherwise
    """
    try:
        # Try stock_zh_a_hist which might include technical indicators
        df = ak.stock_zh_a_hist(
            symbol=stock_code,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="",
        )

        if df.empty:
            return None

        # Check if MA/EMA columns exist
        ma_ema_cols = [col for col in df.columns if "MA" in str(col) or "EMA" in str(col)]
        if ma_ema_cols:
            return df

        return None
    except Exception:
        return None


def get_stock_ma_ema(
    stock_code: str,
    start_date: str,
    end_date: str,
    ma_periods: list[int] | None = None,
    ema_periods: list[int] | None = None,
    prefer_akshare: bool = False,
) -> pd.DataFrame:
    """
    Get MA/EMA values for a stock, trying akshare first, then computing locally.

    Args:
        stock_code: Stock code (e.g., "600036")
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format
        ma_periods: List of MA periods to compute
        ema_periods: List of EMA periods to compute
        prefer_akshare: If True, try akshare first; if False, compute locally

    Returns:
        DataFrame with MA and EMA columns
    """
    if prefer_akshare:
        # Try fetching from akshare first
        df = fetch_ma_ema_from_akshare(stock_code, start_date, end_date)
        if df is not None:
            return df

    # Fetch stock data and compute locally
    df = download_daily(stock_code, start_date, end_date)
    df = compute_ma_ema_local(df, ma_periods=ma_periods, ema_periods=ema_periods)

    return df


def process_watchlist(
    watchlist_name: str = "default",
    start_date: str | None = None,
    end_date: str | None = None,
    ma_periods: list[int] | None = None,
    ema_periods: list[int] | None = None,
    show_summary: bool = True,
) -> dict[str, pd.DataFrame]:
    """
    Process all stocks in a watchlist and compute MA/EMA values.

    Args:
        watchlist_name: Name of the watchlist
        start_date: Start date in YYYYMMDD format (default: 200 days ago)
        end_date: End date in YYYYMMDD format (default: today)
        ma_periods: List of MA periods to compute
        ema_periods: List of EMA periods to compute
        show_summary: If True, print summary for each stock

    Returns:
        Dictionary mapping stock codes to DataFrames with MA/EMA values
    """
    from datetime import datetime, timedelta

    # Set default dates if not provided
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")
    if start_date is None:
        start_date_dt = datetime.now() - timedelta(days=200)
        start_date = start_date_dt.strftime("%Y%m%d")

    # Get stocks from watchlist
    stocks = get_watchlist(watchlist_name)
    results = {}

    print(f"📊 Processing {len(stocks)} stocks from watchlist '{watchlist_name}'")
    print(f"   Date range: {start_date} to {end_date}")
    print("=" * 80)

    for i, stock_code in enumerate(stocks, 1):
        try:
            print(f"[{i}/{len(stocks)}] Processing {stock_code}...", end=" ", flush=True)
            df = get_stock_ma_ema(
                stock_code,
                start_date,
                end_date,
                ma_periods=ma_periods,
                ema_periods=ema_periods,
                prefer_akshare=False,  # Compute locally for consistency
            )

            results[stock_code] = df

            if show_summary:
                # Show latest values
                latest = df.tail(1)
                if not latest.empty:
                    close = latest["close"].iloc[0]
                    ma_cols = [col for col in df.columns if col.startswith("MA")]
                    ema_cols = [col for col in df.columns if col.startswith("EMA")]

                    ma_values = {col: latest[col].iloc[0] for col in ma_cols if col in latest.columns}
                    ema_values = {col: latest[col].iloc[0] for col in ema_cols if col in latest.columns}

                    print(f"✅ Close: {close:.2f}", end="")
                    if ma_values:
                        ma_str = ", ".join([f"{k}={v:.2f}" for k, v in list(ma_values.items())[:2]])
                        print(f" | MA: {ma_str}", end="")
                    if ema_values:
                        ema_str = ", ".join([f"{k}={v:.2f}" for k, v in list(ema_values.items())[:2]])
                        print(f" | EMA: {ema_str}", end="")
                    print()
                else:
                    print("✅ (no data)")
            else:
                print("✅")

        except Exception as e:
            print(f"❌ Error: {e}")
            results[stock_code] = None

    print("=" * 80)
    print(f"✅ Processed {len([r for r in results.values() if r is not None])}/{len(stocks)} stocks")

    return results


def main():
    """Main function to compute MA/EMA for stocks."""
    import argparse

    parser = argparse.ArgumentParser(description="Compute or fetch MA/EMA values for stocks")
    parser.add_argument(
        "--watchlist",
        type=str,
        default="default",
        help="Watchlist name (default: default)",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date in YYYYMMDD format (default: 200 days ago)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date in YYYYMMDD format (default: today)",
    )
    parser.add_argument(
        "--ma-periods",
        type=str,
        default="5,10,20,30,60",
        help="Comma-separated MA periods (default: 5,10,20,30,60)",
    )
    parser.add_argument(
        "--ema-periods",
        type=str,
        default="5,10,20,30,60",
        help="Comma-separated EMA periods (default: 5,10,20,30,60)",
    )
    parser.add_argument(
        "--stock",
        type=str,
        help="Process a single stock code instead of watchlist",
    )

    args = parser.parse_args()

    # Parse periods
    ma_periods = [int(p) for p in args.ma_periods.split(",")]
    ema_periods = [int(p) for p in args.ema_periods.split(",")]

    if args.stock:
        # Process single stock
        from datetime import datetime, timedelta

        end_date = args.end_date or datetime.now().strftime("%Y%m%d")
        start_date = args.start_date or (datetime.now() - timedelta(days=200)).strftime("%Y%m%d")

        print(f"📊 Processing single stock: {args.stock}")
        df = get_stock_ma_ema(
            args.stock,
            start_date,
            end_date,
            ma_periods=ma_periods,
            ema_periods=ema_periods,
        )

        print("\n" + "=" * 80)
        print(f"📈 MA/EMA Values for {args.stock}")
        print("=" * 80)
        print(
            df[["date", "close"] + [col for col in df.columns if "MA" in col or "EMA" in col]]
            .tail(10)
            .to_string(index=False)
        )
    else:
        # Process watchlist
        results = process_watchlist(
            watchlist_name=args.watchlist,
            start_date=args.start_date,
            end_date=args.end_date,
            ma_periods=ma_periods,
            ema_periods=ema_periods,
        )

        # Show summary
        print("\n" + "=" * 80)
        print("📊 Summary")
        print("=" * 80)
        for stock_code, df in results.items():
            if df is not None:
                print(f"\n{stock_code}: {len(df)} days of data")
                print(f"  Columns: {', '.join([col for col in df.columns if 'MA' in col or 'EMA' in col])}")


if __name__ == "__main__":
    main()
