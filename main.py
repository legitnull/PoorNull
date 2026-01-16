"""Fetch stock data and compute MA/EMA indicators for different timeframes."""

import logging
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import pandas as pd

from poornull.data import Period, PriceHistory, download_daily, download_monthly, download_weekly
from poornull.indicators import (
    TomDemarkSequentialPhase,
    calculate_ma_ema,
    calculate_tomdemark_sequential,
    calculate_weekly_ma,
    find_ma_above_ma60,
    find_ma_crossovers,
    find_macd_crossovers,
    tonghuashun_macd,
)
from poornull.rules import evaluate_daily_ma250_no_action

logger = logging.getLogger(__name__)


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
        logger.error(f"No data found for stock {stock_code}")
        return None

    logger.info(f"Columns returned by akshare-one for stock {stock_code}:")
    logger.info(f"   Total columns: {len(stock_data.columns)}")
    logger.info(f"   Column names: {list(stock_data.columns)}")
    logger.info("Sample data (first 3 rows):")
    logger.info(f"\n{stock_data.head(3).to_string()}")

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
        logger.info(f"Found potential technical indicator columns: {found_indicators}")
    else:
        logger.info("Use akshare_one.indicators functions to add technical indicators")

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

    logger.info(f"Fetching stock {stock_code} data from {start_date_formatted} to {end_date_formatted}...")
    logger.info("   Using unadjusted prices (as Tonghuashun does for MACD)")

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
    logger.info("Calculating MACD using Tonghuashun method (12, 26, 9, 2x multiplier)...")
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

    logger.info(f"Fetching {period_name} data for {stock_code}")
    logger.info(f"   Date range: {start_date_str} to {end_date_str} (last {days_back} {period_name.lower()}s)")

    # Download data based on period
    if period == Period.DAILY:
        df = download_daily(stock_code, start_date_str, end_date_str)
    elif period == Period.WEEKLY:
        df = download_weekly(stock_code, start_date_str, end_date_str)
    elif period == Period.MONTHLY:
        df = download_monthly(stock_code, start_date_str, end_date_str)
    else:
        df = download_daily(stock_code, start_date_str, end_date_str)

    logger.info(f"Fetched {len(df)} records")

    # Calculate MA and EMA
    logger.info("Calculating MA and EMA...")
    df = calculate_ma_ema(df, ma_periods=ma_periods, ema_periods=ema_periods)

    return df


def main():
    """Main function to fetch data and compute MA/EMA for different timeframes."""
    stock_code = "600036"  # Default stock: 招商银行

    logger.info("=" * 80)
    logger.info("Stock MA/EMA Calculator")
    logger.info("=" * 80)
    logger.info(f"Stock: {stock_code}")
    logger.info("Fetching last 1000 days/weeks/months till today")

    try:
        # Process daily data
        logger.info("\n" + "=" * 80)
        logger.info("DAILY DATA (日线)")
        logger.info("=" * 80)
        daily_df = process_stock_ma_ema(
            stock_code,
            Period.DAILY,
            days_back=1000,
            ma_periods=[5, 10, 20, 30, 60, 250],
        )

        # Show latest values
        ma_cols = [col for col in daily_df.columns if col.startswith("MA")]
        ema_cols = [col for col in daily_df.columns if col.startswith("EMA")]
        display_cols = ["date", "close"] + ma_cols[:3] + ema_cols[:3]  # Show first 3 of each

        logger.info("Latest Daily MA/EMA Values:")
        logger.info(f"\n{daily_df[display_cols].tail(10).to_string(index=False)}")

        # Evaluate trading rules using PriceHistory API
        daily_history = PriceHistory(daily_df)
        signal = evaluate_daily_ma250_no_action(daily_history)
        if signal:
            emoji = {"info": "ℹ️", "warning": "⚠️", "action": "🎯"}[signal.severity]
            logger.warning(f"{emoji} {signal.message}")
            if signal.metadata:
                logger.info(f"   Close: {signal.metadata['close']:.2f}")
                logger.info(f"   MA250: {signal.metadata['ma250']:.2f}")
                logger.info(f"   Distance: {signal.metadata['distance_pct']:.2f}%")

        # Process weekly data
        logger.info("\n" + "=" * 80)
        logger.info("WEEKLY DATA (周线)")
        logger.info("=" * 80)
        weekly_df = process_stock_ma_ema(stock_code, Period.WEEKLY, days_back=1000)

        logger.info("Latest Weekly MA/EMA Values:")
        logger.info(f"\n{weekly_df[display_cols].tail(10).to_string(index=False)}")

        # Process monthly data
        logger.info("\n" + "=" * 80)
        logger.info("MONTHLY DATA (月线)")
        logger.info("=" * 80)
        monthly_df = process_stock_ma_ema(stock_code, Period.MONTHLY, days_back=1000)

        logger.info("Latest Monthly MA/EMA Values:")
        logger.info(f"\n{monthly_df[display_cols].tail(10).to_string(index=False)}")

        # Process weekly MA crossovers
        logger.info("\n" + "=" * 80)
        logger.info("WEEKLY MA CROSSOVERS ANALYSIS")
        logger.info("=" * 80)

        # Calculate weekly MA with specific periods
        weekly_ma_df = calculate_weekly_ma(weekly_df, periods=[20, 30, 60, 120, 250])

        # Find crossovers
        crossovers = find_ma_crossovers(weekly_ma_df)

        if crossovers.empty:
            logger.warning("No MA crossovers found")
        else:
            logger.info(f"Found {len(crossovers)} MA crossover(s):\n")
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

                logger.info(f"{cross_symbol} {cross_name}")
                logger.info(f"   Date: {row['date']}")
                logger.info(f"   MA20: {row['ma20']:.2f}")
                logger.info(f"   MA30: {row['ma30']:.2f}")
                logger.info(f"   MA60: {row['ma60']:.2f}")
                if pd.notna(row.get("close_price")):
                    logger.info(f"   Close Price: {row['close_price']:.2f}")
                logger.info("")

        # Find periods where MA20 or MA30 beats MA60
        above_periods = find_ma_above_ma60(weekly_ma_df)

        if above_periods.empty:
            logger.warning("No periods where MA20 or MA30 is above MA60")
        else:
            logger.info(f"Found {len(above_periods)} periods where MA20 or MA30 beats MA60")
            logger.info("Latest periods (last 10):")
            display_cols = ["date", "ma20_above", "ma30_above", "ma20", "ma30", "ma60"]
            if "close_price" in above_periods.columns:
                display_cols.append("close_price")
            logger.info(f"\n{above_periods[display_cols].tail(10).to_string(index=False)}")

        # Comprehensive visualization with all indicators on same graph
        logger.info("\n" + "=" * 80)
        logger.info("COMPREHENSIVE STOCK ANALYSIS CHART")
        logger.info("=" * 80)

        # Calculate TomDeMark Sequential for daily data
        logger.info("Calculating TomDeMark Sequential for daily data...")
        daily_td = calculate_tomdemark_sequential(daily_df)

        # Show recent TD Sequential activity
        recent_td = daily_td[(daily_td["TD_Setup_Count"] > 0) | (daily_td["TD_Countdown_Count"] > 0)].tail(15)

        if not recent_td.empty:
            logger.info("Recent TD Sequential Activity (last 15 active bars):")
            display_cols = ["date", "close", "TD_Phase_Name", "TD_Setup_Count", "TD_Countdown_Count"]
            logger.info(f"\n{recent_td[display_cols].to_string(index=False)}")
        else:
            logger.warning("No active TD Sequential phases in recent data")

        # Find completed setups
        completed_setups = daily_td[
            (daily_td["TD_Setup_Count"] == 9) & (daily_td["TD_Phase"] != TomDemarkSequentialPhase.NONE)
        ]

        if not completed_setups.empty:
            logger.info(f"Found {len(completed_setups)} completed setup(s):")
            for _, row in completed_setups.tail(5).iterrows():
                phase_name = row["TD_Phase_Name"]
                symbol = "🟢" if "Buy" in phase_name else "🔴"
                logger.info(f"{symbol} {phase_name} on {row['date']} at price {row['close']:.2f}")

        # Find completed countdowns
        completed_countdowns = daily_td[daily_td["TD_Countdown_Count"] == 13]

        if not completed_countdowns.empty:
            logger.info(f"Found {len(completed_countdowns)} completed countdown(s) (strong reversal signal):")
            for _, row in completed_countdowns.tail(3).iterrows():
                phase_name = row["TD_Phase_Name"]
                symbol = "🟢" if "Buy" in phase_name else "🔴"
                logger.info(f"{symbol} {phase_name} on {row['date']} at price {row['close']:.2f}")

        # Generate comprehensive visualization with all indicators
        logger.info("Generating comprehensive chart with all indicators...")
        try:
            from poornull.visualize import (
                create_figure,
                format_date_axis,
                get_date_column,
                plot_candlesticks,
                plot_moving_averages,
                plot_tomdemark_counters,
                plot_tomdemark_sequential,
                plot_trendlines,
                save_or_show,
                setup_style,
            )

            # Use last 365 days for better visualization
            end_date_str = datetime.now().strftime("%Y%m%d")
            start_date_str = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

            # Get data for visualization period
            from poornull.data import download_daily

            viz_df = download_daily(stock_code, start_date_str, end_date_str)
            viz_df = calculate_ma_ema(viz_df, ma_periods=[5, 10, 20, 30, 60])
            viz_df = calculate_tomdemark_sequential(viz_df)

            # Setup style
            setup_style(figsize=(18, 12))

            # Create figure with 2 subplots: main chart + TD counters
            fig, axes = create_figure(nrows=2, ncols=1, height_ratios=[3, 1], sharex=True)

            # Ensure we have at least 2 axes
            if len(axes) < 2:
                raise ValueError(f"Expected 2 axes, got {len(axes)}")

            ax_main, ax_counters = axes[0], axes[1]

            date_col = get_date_column(viz_df)
            if date_col is None:
                raise ValueError("Could not find date column in DataFrame")

            # Main chart: Candlesticks + MA + Trendlines + TD Sequential
            plot_candlesticks(
                ax_main,
                viz_df,
                date_col=date_col,
                open_col="open",
                high_col="high",
                low_col="low",
                close_col="close",
            )

            # Plot moving averages
            plot_moving_averages(ax_main, viz_df, date_col=date_col, ma_periods=[5, 10, 20, 30, 60])

            # Plot trendlines
            plot_trendlines(ax_main, viz_df, date_col=date_col, method="linear", label="Linear Trend")

            # Plot TomDeMark Sequential phases
            plot_tomdemark_sequential(ax_main, viz_df, date_col=date_col, show_annotations=True)

            # Set title and format main chart
            ax_main.set_title(
                f"Comprehensive Stock Analysis - {stock_code} ({start_date_str} to {end_date_str})",
                fontsize=16,
                fontweight="bold",
            )
            ax_main.set_ylabel("Price", fontsize=12, fontweight="bold")
            ax_main.set_xlabel("Date", fontsize=12, fontweight="bold")
            ax_main.legend(loc="best", fontsize=9, ncol=2)
            ax_main.grid(True, alpha=0.3)

            # Format date axis for main chart
            format_date_axis(ax_main, date_col, viz_df)

            # Bottom chart: TD Sequential counters
            plot_tomdemark_counters(ax_counters, viz_df, date_col=date_col)
            ax_counters.set_xlabel("Date", fontsize=12, fontweight="bold")
            format_date_axis(ax_counters, date_col, viz_df)

            plt.tight_layout()

            # Save and show
            save_or_show(fig, save_path="comprehensive_stock_chart.png", show=True)

            logger.info("Comprehensive chart saved to comprehensive_stock_chart.png")
            logger.info("   Chart includes:")
            logger.info("   - Candlestick chart (OHLC)")
            logger.info("   - Moving Averages (MA5, MA10, MA20, MA30, MA60)")
            logger.info("   - Linear trendline")
            logger.info("   - TomDeMark Sequential phases (Buy/Sell Setup, Countdown)")
            logger.info("   - TD Sequential counters (bottom panel)")

        except Exception as e:
            logger.warning(f"Could not generate visualization: {e}")
            import traceback

            traceback.print_exc()
            logger.info("   (This is okay - you can run demo_tomdemark_sequential() separately)")

        logger.info("\n" + "=" * 80)
        logger.info("All calculations complete!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)


def test_macd():
    """Test MACD calculation and crossover detection."""
    logger.info("Testing MACD calculation and crossover detection...")
    logger.info("=" * 60)

    stock_code = "600036"
    start_date = "20240101"
    end_date = "20260109"

    try:
        stock_data, crossovers = get_stock_macd_crossovers(stock_code, start_date, end_date)

        logger.info(f"Successfully calculated MACD for stock {stock_code}")
        logger.info(f"   Data period: {start_date} to {end_date}")
        logger.info(f"   Total records: {len(stock_data)}")

        if crossovers.empty:
            logger.warning("No MACD crossovers found in this period")
        else:
            logger.info(f"Found {len(crossovers)} MACD crossover(s):\n")
            for _, row in crossovers.iterrows():
                cross_type = row["type"]
                cross_symbol = "🟢" if cross_type == "golden" else "🔴"
                cross_name = "Golden Cross (Bullish)" if cross_type == "golden" else "Death Cross (Bearish)"
                logger.info(f"{cross_symbol} {cross_name}")
                logger.info(f"   Date: {row['date']}")
                logger.info(f"   DIF: {row['dif']:.4f}")
                logger.info(f"   DEA: {row['dea']:.4f}")
                if "macd" in row:
                    logger.info(f"   MACD (Histogram): {row['macd']:.4f}")
                if "close_price" in row:
                    logger.info(f"   Close Price: {row['close_price']:.2f}")
                logger.info("")

        # Show latest MACD values
        logger.info("Latest MACD values:")
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
                logger.info(f"\n{latest.to_string(index=False)}")

    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)


def visualize_tomdemark_sequential(stock_code: str, start_date: str, end_date: str, save_path: str | None = None):
    """
    Visualize TomDeMark Sequential indicator with price chart and phase annotations.

    Args:
        stock_code: Stock code (e.g., "600036")
        start_date: Start date in format "YYYYMMDD"
        end_date: End date in format "YYYYMMDD"
        save_path: Optional path to save the figure (e.g., "td_sequential_chart.png")
    """
    from poornull.data import download_daily
    from poornull.visualize import create_tomdemark_chart

    logger.info(f"Visualizing TomDeMark Sequential for {stock_code}")
    logger.info(f"   Date range: {start_date} to {end_date}")

    # Download data
    df = download_daily(stock_code, start_date, end_date)
    if df.empty:
        logger.error(f"No data found for stock {stock_code}")
        return

    # Calculate TomDeMark Sequential
    logger.info("Calculating TomDeMark Sequential...")
    df = calculate_tomdemark_sequential(df)

    # Create chart using modular visualization
    if save_path is None:
        save_path = "tomdemark_sequential_chart.png"

    create_tomdemark_chart(df, stock_code, start_date, end_date, save_path=save_path, show=True)

    # Print summary statistics
    logger.info("TD Sequential Summary:")
    logger.info(f"   Total bars analyzed: {len(df)}")
    logger.info(f"   Buy Setups completed: {len(df[df['TD_Setup_Count'] == 9])}")
    logger.info(f"   Sell Setups completed: {len(df[(df['TD_Setup_Count'] == 9) & (df['TD_Phase'].isin([2, 6]))])}")
    logger.info(f"   Buy Countdowns completed: {len(df[(df['TD_Countdown_Count'] == 13) & (df['TD_Phase'] == 3)])}")
    logger.info(f"   Sell Countdowns completed: {len(df[(df['TD_Countdown_Count'] == 13) & (df['TD_Phase'] == 4)])}")

    # Show recent activity
    date_col = None
    for col in df.columns:
        col_lower = str(col).lower()
        if "date" in col_lower or "timestamp" in col_lower or "日期" in str(col):
            date_col = col
            break

    if date_col:
        recent_activity = df[(df["TD_Setup_Count"] > 0) | (df["TD_Countdown_Count"] > 0)].tail(10)
        if not recent_activity.empty:
            logger.info("Recent TD Sequential Activity:")
            display_cols = [date_col, "close", "TD_Phase_Name", "TD_Setup_Count", "TD_Countdown_Count"]
            logger.info(f"\n{recent_activity[display_cols].to_string(index=False)}")


def demo_tomdemark_sequential():
    """Demonstrate TomDeMark Sequential visualization."""
    logger.info("=" * 80)
    logger.info("TomDeMark Sequential Indicator Visualization")
    logger.info("=" * 80)

    stock_code = "600036"  # 招商银行
    start_date = "20240101"
    end_date = datetime.now().strftime("%Y%m%d")

    try:
        visualize_tomdemark_sequential(stock_code, start_date, end_date)
    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)


if __name__ == "__main__":
    # Uncomment the line below to run TD Sequential visualization
    # demo_tomdemark_sequential()
    main()
