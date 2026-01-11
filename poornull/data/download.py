"""
Data download functions for different timeframes.

This module provides functions to download stock market data for:
- Daily data (日线)
- Weekly data (周线)
- Monthly data (月线)
- Quarterly data (季线)
"""

from enum import Enum

import akshare as ak
import pandas as pd

from .constants import AKSHARE_COLUMN_MAPPING


class Period(str, Enum):
    """Timeframe period for stock data."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


def download_stock_data(
    stock_code: str,
    start_date: str,
    end_date: str,
    period: Period = Period.DAILY,
    adjust: str = "",
) -> pd.DataFrame:
    """
    Download stock market data for the specified timeframe.

    Args:
        stock_code: Stock code (e.g., "600036")
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format
        period: Timeframe period. Options:
            - Period.DAILY: Daily data (日线) - default
            - Period.WEEKLY: Weekly data (周线)
            - Period.MONTHLY: Monthly data (月线)
            - Period.QUARTERLY: Quarterly data (季线)
        adjust: Price adjustment type. Options:
            - "" (empty string): Unadjusted (不复权) - default
            - "qfq": Forward adjusted (前复权)
            - "hfq": Backward adjusted (后复权)

    Returns:
        DataFrame with columns:
        - date: Date (datetime)
        - open: Opening price
        - close: Closing price
        - high: Highest price
        - low: Lowest price
        - volume: Trading volume
        - amount: Trading amount (成交额)
        - amplitude: Amplitude (振幅)
        - pct_change: Percentage change (涨跌幅)
        - change: Price change (涨跌额)
        - turnover: Turnover rate (换手率)

    Example:
        >>> # Download daily data
        >>> df = download_stock_data("600036", "20240101", "20241231", period=Period.DAILY)
        >>> # Download weekly data
        >>> df = download_stock_data("600036", "20240101", "20241231", period=Period.WEEKLY)
        >>> # Download monthly data
        >>> df = download_stock_data("600036", "20240101", "20241231", period=Period.MONTHLY)
        >>> # Download quarterly data
        >>> df = download_stock_data("600036", "20240101", "20241231", period=Period.QUARTERLY)
    """
    # Fetch data
    df = ak.stock_zh_a_hist(
        symbol=stock_code,
        period=period.value,
        start_date=start_date,
        end_date=end_date,
        adjust=adjust,
    )

    if df.empty:
        raise ValueError(f"No data found for stock {stock_code}")

    # Convert column names to English
    df = df.rename(columns=AKSHARE_COLUMN_MAPPING)

    # Convert date to datetime
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])

    # Sort by date
    if "date" in df.columns:
        df = df.sort_values(by="date")

    return df


def download_daily(
    stock_code: str,
    start_date: str,
    end_date: str,
    adjust: str = "",
) -> pd.DataFrame:
    """
    Download daily stock data (convenience wrapper).

    Args:
        stock_code: Stock code (e.g., "600036")
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format
        adjust: Price adjustment type. Options:
            - "" (empty string): Unadjusted (不复权) - default
            - "qfq": Forward adjusted (前复权)
            - "hfq": Backward adjusted (后复权)

    Returns:
        DataFrame with stock data (see download_stock_data for details).

    Example:
        >>> df = download_daily("600036", "20240101", "20241231")
    """
    return download_stock_data(stock_code, start_date, end_date, period=Period.DAILY, adjust=adjust)


def download_weekly(
    stock_code: str,
    start_date: str,
    end_date: str,
    adjust: str = "",
) -> pd.DataFrame:
    """
    Download weekly stock data (convenience wrapper).

    Args:
        stock_code: Stock code (e.g., "600036")
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format
        adjust: Price adjustment type. Options:
            - "" (empty string): Unadjusted (不复权) - default
            - "qfq": Forward adjusted (前复权)
            - "hfq": Backward adjusted (后复权)

    Returns:
        DataFrame with stock data (see download_stock_data for details).

    Example:
        >>> df = download_weekly("600036", "20240101", "20241231")
    """
    return download_stock_data(stock_code, start_date, end_date, period=Period.WEEKLY, adjust=adjust)


def download_monthly(
    stock_code: str,
    start_date: str,
    end_date: str,
    adjust: str = "",
) -> pd.DataFrame:
    """
    Download monthly stock data (convenience wrapper).

    Args:
        stock_code: Stock code (e.g., "600036")
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format
        adjust: Price adjustment type. Options:
            - "" (empty string): Unadjusted (不复权) - default
            - "qfq": Forward adjusted (前复权)
            - "hfq": Backward adjusted (后复权)

    Returns:
        DataFrame with stock data (see download_stock_data for details).

    Example:
        >>> df = download_monthly("600036", "20240101", "20241231")
    """
    return download_stock_data(stock_code, start_date, end_date, period=Period.MONTHLY, adjust=adjust)


def download_quarterly(
    stock_code: str,
    start_date: str,
    end_date: str,
    adjust: str = "",
) -> pd.DataFrame:
    """
    Download quarterly stock data (convenience wrapper).

    Args:
        stock_code: Stock code (e.g., "600036")
        start_date: Start date in YYYYMMDD format
        end_date: End date in YYYYMMDD format
        adjust: Price adjustment type. Options:
            - "" (empty string): Unadjusted (不复权) - default
            - "qfq": Forward adjusted (前复权)
            - "hfq": Backward adjusted (后复权)

    Returns:
        DataFrame with stock data (see download_stock_data for details).

    Example:
        >>> df = download_quarterly("600036", "20240101", "20241231")
    """
    return download_stock_data(stock_code, start_date, end_date, period=Period.QUARTERLY, adjust=adjust)
