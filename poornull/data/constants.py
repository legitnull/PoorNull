"""
Constants for data download and processing.

This module contains mappings and constants used across the data module.
"""

# Column name mapping from Chinese (akshare) to English
AKSHARE_COLUMN_MAPPING = {
    "日期": "date",
    "收盘": "close",
    "开盘": "open",
    "最高": "high",
    "最低": "low",
    "成交量": "volume",
    "成交额": "amount",
    "振幅": "amplitude",
    "涨跌幅": "pct_change",
    "涨跌额": "change",
    "换手率": "turnover",
}
