"""Technical indicators for stock analysis."""

from .ma_ema import (
    calculate_ema,
    calculate_ma,
    calculate_ma_ema,
    with_ema,
    with_ma,
    with_ma_ema,
)
from .macd import (
    calculate_tonghuashun_macd,
    find_macd_crossovers,
    tonghuashun_macd,
    with_macd,
)
from .tomdemark_sequential import (
    TomDemarkSequentialPhase,
    calculate_tomdemark_sequential,
    with_tomdemark,
)
from .weekly_ma_crossovers import (
    calculate_weekly_ma,
    find_ma_above_ma60,
    find_ma_crossovers,
)

__all__ = [
    # DataFrame API (legacy)
    "tonghuashun_macd",
    "calculate_tonghuashun_macd",
    "find_macd_crossovers",
    "calculate_ma",
    "calculate_ema",
    "calculate_ma_ema",
    "calculate_weekly_ma",
    "find_ma_crossovers",
    "find_ma_above_ma60",
    "calculate_tomdemark_sequential",
    "TomDemarkSequentialPhase",
    # PriceHistory API (new)
    "with_ma",
    "with_ema",
    "with_ma_ema",
    "with_macd",
    "with_tomdemark",
]
