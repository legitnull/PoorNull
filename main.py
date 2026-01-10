"""Simple script to verify akshare-one API and demonstrate MACD calculation."""

import pandas as pd
from akshare_one import get_hist_data

from poornull.indicators import find_macd_crossovers, tonghuashun_macd


def inspect_akshare_one_columns(stock_code, start_date, end_date):
    """
    Inspect what columns akshare-one returns for a stock.
    Useful to check available technical indicators.

    Args:
        stock_code: Stock code (e.g., "600036")
        start_date: Start date in format "YYYYMMDD"
        end_date: End date in format "YYYYMMDD"

    Returns:
        DataFrame with sample data and column information
    """
    # Convert date format
    start_date_formatted = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:8]}"
    end_date_formatted = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:8]}"

    stock_data = get_hist_data(
        symbol=stock_code, interval="day", start_date=start_date_formatted, end_date=end_date_formatted
    )

    if stock_data.empty:
        print(f"❌ No data found for stock {stock_code}")
        return None

    print(f"\n📋 Columns returned by akshare-one for stock {stock_code}:")
    print(f"   Total columns: {len(stock_data.columns)}")
    print(f"   Column names: {list(stock_data.columns)}")
    print("\n📊 Sample data (first 3 rows):")
    print(stock_data.head(3).to_string())

    # Check for common technical indicator keywords
    tech_indicators = ["MACD", "RSI", "KDJ", "BOLL", "MA", "EMA", "VOL"]
    found_indicators = []
    for col in stock_data.columns:
        col_str = str(col).upper()
        for indicator in tech_indicators:
            if indicator in col_str:
                found_indicators.append(col)
                break

    if found_indicators:
        print(f"\n✅ Found potential technical indicator columns: {found_indicators}")
    else:
        print("\n📊 Use akshare_one.indicators functions to add technical indicators")

    return stock_data


# MACD calculation and crossover detection are now in the indicators module


def get_stock_macd_crossovers(stock_code: str, start_date: str, end_date: str):
    """
    Retrieve stock data, calculate Tonghuashun MACD, and find crossovers.

    Args:
        stock_code: Stock code (e.g., "600036")
        start_date: Start date in format "YYYYMMDD"
        end_date: End date in format "YYYYMMDD"

    Returns:
        Tuple of (stock_data_with_macd, crossovers_df)
    """
    # Fetch stock data using akshare-one
    start_date_formatted = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:8]}"
    end_date_formatted = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:8]}"

    print(f"📊 Fetching stock {stock_code} data from {start_date_formatted} to {end_date_formatted}...")
    print("   Using unadjusted prices (as Tonghuashun does for MACD)")

    try:
        stock_data = get_hist_data(
            symbol=stock_code,
            interval="day",
            start_date=start_date_formatted,
            end_date=end_date_formatted,
            adjust="",  # Try unadjusted
        )
    except (TypeError, KeyError):
        stock_data = get_hist_data(
            symbol=stock_code, interval="day", start_date=start_date_formatted, end_date=end_date_formatted
        )

    if stock_data.empty:
        raise ValueError(f"No data found for stock {stock_code}")

    # Rename timestamp to date if needed
    if "timestamp" in stock_data.columns:
        stock_data = stock_data.rename(columns={"timestamp": "date"})
        stock_data["date"] = pd.to_datetime(stock_data["date"])

    # Calculate MACD using Tonghuashun method
    print("📊 Calculating MACD using Tonghuashun method (12, 26, 9, 2x multiplier)...")
    stock_data_with_macd = tonghuashun_macd(
        stock_data, close_col="close", fast=12, slow=26, signal=9, histogram_multiplier=2.0
    )

    # Find crossovers
    crossovers = find_macd_crossovers(stock_data_with_macd, dif_col="DIF", dea_col="DEA")

    return stock_data_with_macd, crossovers


def main():
    """Query stock 600036 closing price and MACD on 2026-01-09."""
    from datetime import datetime, timedelta

    stock_code = "600036"
    target_date = "2026-01-09"

    print("Querying stock 600036 closing price on 2026-01-09...")
    print("-" * 50)

    try:
        # Fetch data around target date
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=1000)).strftime("%Y-%m-%d")

        print(f"\n📊 Fetching stock {stock_code} data...")
        print(f"   Date range: {start_date} to {end_date} (last 1000 days)")

        stock_data = get_hist_data(symbol=stock_code, interval="day", start_date=start_date, end_date=end_date)

        if stock_data.empty:
            print(f"❌ Failed to fetch data for stock {stock_code}")
            return

        # Rename timestamp to date
        if "timestamp" in stock_data.columns:
            stock_data = stock_data.rename(columns={"timestamp": "date"})
            stock_data["date"] = pd.to_datetime(stock_data["date"])

        print(f"✅ Successfully fetched {len(stock_data)} records")

        # Calculate MACD
        print("\n📊 Calculating MACD using Tonghuashun method...")
        stock_data = tonghuashun_macd(
            stock_data, close_col="close", fast=12, slow=26, signal=9, histogram_multiplier=2.0
        )

        # Find target date
        target_datetime = pd.to_datetime(target_date)
        stock_data["_date_only"] = pd.to_datetime(stock_data["date"]).dt.date
        target_date_only = target_datetime.date()
        target_row = stock_data[stock_data["_date_only"] == target_date_only]
        stock_data = stock_data.drop(columns=["_date_only"])

        if target_row.empty:
            print(f"\n⚠️  No data found for {target_date}")
            print("\nAvailable dates (last 10):")
            print(stock_data[["date"]].tail(10))
        else:
            print(f"\n✅ Found data for {target_date}:")
            row = target_row.iloc[0]
            print(f"   Close: {row['close']:.2f}")
            print(f"   DIF: {row['DIF']:.4f}")
            print(f"   DEA: {row['DEA']:.4f}")
            print(f"   MACD: {row['MACD']:.4f}")

    except Exception as e:
        print(f"❌ Error occurred: {e}")
        import traceback

        traceback.print_exc()


def test_macd():
    """Test MACD calculation and crossover detection."""
    print("Testing MACD calculation and crossover detection...")
    print("=" * 60)

    stock_code = "600036"
    start_date = "20240101"
    end_date = "20260109"

    try:
        stock_data, crossovers = get_stock_macd_crossovers(stock_code, start_date, end_date)

        print(f"\n✅ Successfully calculated MACD for stock {stock_code}")
        print(f"   Data period: {start_date} to {end_date}")
        print(f"   Total records: {len(stock_data)}")

        if crossovers.empty:
            print("\n⚠️  No MACD crossovers found in this period")
        else:
            print(f"\n📊 Found {len(crossovers)} MACD crossover(s):\n")
            for _, row in crossovers.iterrows():
                cross_type = row["type"]
                cross_symbol = "🟢" if cross_type == "golden" else "🔴"
                cross_name = "Golden Cross (Bullish)" if cross_type == "golden" else "Death Cross (Bearish)"
                print(f"{cross_symbol} {cross_name}")
                print(f"   Date: {row['date']}")
                print(f"   DIF: {row['dif']:.4f}")
                print(f"   DEA: {row['dea']:.4f}")
                if "macd" in row:
                    print(f"   MACD (Histogram): {row['macd']:.4f}")
                if "close_price" in row:
                    print(f"   Close Price: {row['close_price']:.2f}")
                print()

        # Show latest MACD values
        print("\nLatest MACD values:")
        date_col = None
        for col in stock_data.columns:
            col_lower = str(col).lower()
            if "timestamp" in col_lower or "date" in col_lower or "日期" in str(col):
                date_col = col
                break
        if date_col:
            # Show DIF, DEA, MACD (Tonghuashun terminology)
            display_cols = [date_col, "DIF", "DEA", "MACD"]
            available_cols = [col for col in display_cols if col in stock_data.columns]
            if available_cols:
                latest = stock_data.tail(5)[available_cols]
                print(latest.to_string(index=False))

    except Exception as e:
        print(f"❌ Error occurred: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Uncomment to test MACD functionality
    test_macd()
    # main()
