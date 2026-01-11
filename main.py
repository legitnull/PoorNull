"""Fetch stock data and compute MA/EMA indicators for different timeframes."""

from datetime import datetime, timedelta

import pandas as pd

from poornull.data import Period, download_daily, download_monthly, download_weekly
from poornull.indicators import (
    calculate_ma_ema,
    calculate_weekly_ma,
    find_ma_above_ma60,
    find_ma_crossovers,
    find_macd_crossovers,
    tonghuashun_macd,
)


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
    from akshare_one import get_hist_data

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
    from akshare_one import get_hist_data

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


def process_stock_ma_ema(
    stock_code: str,
    period: Period = Period.DAILY,
    days_back: int = 1000,
    ma_periods: list[int] | None = None,
    ema_periods: list[int] | None = None,
) -> pd.DataFrame:
    """
    Fetch stock data and compute MA/EMA for specified timeframe.

    Args:
        stock_code: Stock code (e.g., "600036")
        period: Timeframe period (DAILY, WEEKLY, or MONTHLY)
        days_back: Number of days/weeks/months to fetch (default: 1000)
        ma_periods: List of MA periods to compute (default: [5, 10, 20, 30, 60])
        ema_periods: List of EMA periods to compute (default: [5, 10, 20, 30, 60])

    Returns:
        DataFrame with MA and EMA columns
    """
    # Calculate date range
    end_date = datetime.now()
    if period == Period.DAILY:
        start_date = end_date - timedelta(days=days_back)
    elif period == Period.WEEKLY:
        start_date = end_date - timedelta(weeks=days_back)
    elif period == Period.MONTHLY:
        # Approximate months as 30 days
        start_date = end_date - timedelta(days=days_back * 30)
    else:
        start_date = end_date - timedelta(days=days_back)

    start_date_str = start_date.strftime("%Y%m%d")
    end_date_str = end_date.strftime("%Y%m%d")

    period_name = period.value.capitalize()

    print(f"📊 Fetching {period_name} data for {stock_code}")
    print(f"   Date range: {start_date_str} to {end_date_str} (last {days_back} {period_name.lower()}s)")

    # Download data based on period
    if period == Period.DAILY:
        df = download_daily(stock_code, start_date_str, end_date_str)
    elif period == Period.WEEKLY:
        df = download_weekly(stock_code, start_date_str, end_date_str)
    elif period == Period.MONTHLY:
        df = download_monthly(stock_code, start_date_str, end_date_str)
    else:
        df = download_daily(stock_code, start_date_str, end_date_str)

    print(f"✅ Fetched {len(df)} records")

    # Calculate MA and EMA
    print("\n📈 Calculating MA and EMA...")
    df = calculate_ma_ema(df, ma_periods=ma_periods, ema_periods=ema_periods)

    return df


def main():
    """Main function to fetch data and compute MA/EMA for different timeframes."""
    stock_code = "600036"  # Default stock: 招商银行

    print("=" * 80)
    print("Stock MA/EMA Calculator")
    print("=" * 80)
    print(f"\nStock: {stock_code}")
    print("Fetching last 1000 days/weeks/months till today")
    print()

    try:
        # Process daily data
        print("\n" + "=" * 80)
        print("📅 DAILY DATA (日线)")
        print("=" * 80)
        daily_df = process_stock_ma_ema(stock_code, Period.DAILY, days_back=1000)

        # Show latest values
        ma_cols = [col for col in daily_df.columns if col.startswith("MA")]
        ema_cols = [col for col in daily_df.columns if col.startswith("EMA")]
        display_cols = ["date", "close"] + ma_cols[:3] + ema_cols[:3]  # Show first 3 of each

        print("\n📊 Latest Daily MA/EMA Values:")
        print(daily_df[display_cols].tail(10).to_string(index=False))

        # Process weekly data
        print("\n" + "=" * 80)
        print("📅 WEEKLY DATA (周线)")
        print("=" * 80)
        weekly_df = process_stock_ma_ema(stock_code, Period.WEEKLY, days_back=1000)

        print("\n📊 Latest Weekly MA/EMA Values:")
        print(weekly_df[display_cols].tail(10).to_string(index=False))

        # Process monthly data
        print("\n" + "=" * 80)
        print("📅 MONTHLY DATA (月线)")
        print("=" * 80)
        monthly_df = process_stock_ma_ema(stock_code, Period.MONTHLY, days_back=1000)

        print("\n📊 Latest Monthly MA/EMA Values:")
        print(monthly_df[display_cols].tail(10).to_string(index=False))

        # Process weekly MA crossovers
        print("\n" + "=" * 80)
        print("📊 WEEKLY MA CROSSOVERS ANALYSIS")
        print("=" * 80)

        # Calculate weekly MA with specific periods
        weekly_ma_df = calculate_weekly_ma(weekly_df, periods=[20, 30, 60, 120, 250])

        # Find crossovers
        crossovers = find_ma_crossovers(weekly_ma_df)

        if crossovers.empty:
            print("\n⚠️  No MA crossovers found")
        else:
            print(f"\n✅ Found {len(crossovers)} MA crossover(s):\n")
            for _, row in crossovers.iterrows():
                cross_type = row["type"]
                if "golden" in cross_type:
                    cross_symbol = "🟢"
                    cross_name = "Golden Cross"
                    ma_type = "MA20" if "ma20" in cross_type else "MA30"
                    cross_name = f"{cross_name} ({ma_type} crosses above MA60)"
                else:
                    cross_symbol = "🔴"
                    cross_name = "Death Cross"
                    ma_type = "MA20" if "ma20" in cross_type else "MA30"
                    cross_name = f"{cross_name} ({ma_type} crosses below MA60)"

                print(f"{cross_symbol} {cross_name}")
                print(f"   Date: {row['date']}")
                print(f"   MA20: {row['ma20']:.2f}")
                print(f"   MA30: {row['ma30']:.2f}")
                print(f"   MA60: {row['ma60']:.2f}")
                if pd.notna(row.get("close_price")):
                    print(f"   Close Price: {row['close_price']:.2f}")
                print()

        # Find periods where MA20 or MA30 beats MA60
        above_periods = find_ma_above_ma60(weekly_ma_df)

        if above_periods.empty:
            print("\n⚠️  No periods where MA20 or MA30 is above MA60")
        else:
            print(f"\n✅ Found {len(above_periods)} periods where MA20 or MA30 beats MA60")
            print("\n📊 Latest periods (last 10):")
            display_cols = ["date", "ma20_above", "ma30_above", "ma20", "ma30", "ma60"]
            if "close_price" in above_periods.columns:
                display_cols.append("close_price")
            print(above_periods[display_cols].tail(10).to_string(index=False))

        print("\n" + "=" * 80)
        print("✅ All calculations complete!")
        print("=" * 80)

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
    main()
