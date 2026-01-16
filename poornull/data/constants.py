"""
Constants for data download and processing.

This module contains mappings and constants used across the data module.
"""

from enum import Enum

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


class IndicatorType(str, Enum):
    """
    Standard technical indicator types.

    For period-based indicators (MA, EMA), use the helper methods:
    - Indicator.ma(250) -> "MA250"
    - Indicator.ema(12) -> "EMA12"
    """

    # MACD indicators
    DIF = "DIF"
    DEA = "DEA"
    MACD = "MACD"

    # TomDeMark Sequential indicators
    TD_PHASE = "TD_Phase"
    TD_SETUP_COUNT = "TD_Setup_Count"
    TD_COUNTDOWN_COUNT = "TD_Countdown_Count"
    TD_SUPPORT_PRICE = "TD_Support_Price"
    TD_RESISTANCE_PRICE = "TD_Resistance_Price"
    TD_PHASE_NAME = "TD_Phase_Name"


class Indicator:
    """
    Helper class for indicator name generation.

    Provides type-safe indicator name generation for both fixed and period-based indicators.

    Examples:
        >>> Indicator.ma(250)
        'MA250'
        >>> Indicator.ema(12)
        'EMA12'
        >>> Indicator.DIF
        'DIF'
        >>> Indicator.TD_PHASE
        'TD_Phase'
    """

    # MACD indicators
    DIF = IndicatorType.DIF.value
    DEA = IndicatorType.DEA.value
    MACD = IndicatorType.MACD.value

    # TomDeMark Sequential indicators
    TD_PHASE = IndicatorType.TD_PHASE.value
    TD_SETUP_COUNT = IndicatorType.TD_SETUP_COUNT.value
    TD_COUNTDOWN_COUNT = IndicatorType.TD_COUNTDOWN_COUNT.value
    TD_SUPPORT_PRICE = IndicatorType.TD_SUPPORT_PRICE.value
    TD_RESISTANCE_PRICE = IndicatorType.TD_RESISTANCE_PRICE.value
    TD_PHASE_NAME = IndicatorType.TD_PHASE_NAME.value

    @staticmethod
    def ma(period: int) -> str:
        """Generate MA indicator name for given period."""
        return f"MA{period}"

    @staticmethod
    def ema(period: int) -> str:
        """Generate EMA indicator name for given period."""
        return f"EMA{period}"
