"""Rule: Signal when all MAs are trending in the same direction."""

import logging

from poornull.data.constants import Indicator
from poornull.data.models import PriceHistory, Signal

logger = logging.getLogger(__name__)


def evaluate_ma_trend_alignment(
    history: PriceHistory,
    periods: list[int] | None = None,
    lookback_bars: int = 1,
) -> Signal | None:
    """
    Evaluate if all MAs are trending in the same direction.

    A strong trend is indicated when all moving averages are aligned
    (all trending up or all trending down).

    Args:
        history: Price history with MA indicators computed
        periods: MA periods to check (default: [5, 10, 20, 30, 60])
        lookback_bars: Number of bars to look back for trend (default: 1)

    Returns:
        Signal if all MAs are trending in same direction, None otherwise
    """
    if periods is None:
        periods = [5, 10, 20, 30, 60]

    # Check if all required MAs exist
    missing_mas = []
    for period in periods:
        ma_name = Indicator.MA(period)
        if not history.has_indicator(ma_name):
            missing_mas.append(ma_name)

    if missing_mas:
        logger.warning(
            f"Required MA indicators not found: {missing_mas}. "
            f"Rule 'ma_trend_alignment' cannot be evaluated. "
            f"Add MAs using: history = with_ma(history, periods={periods})"
        )
        return None

    # Need at least lookback_bars + 1 data points
    if len(history) < lookback_bars + 1:
        logger.warning(
            f"Insufficient data for trend analysis. Need at least {lookback_bars + 1} bars, got {len(history)}"
        )
        return None

    # Analyze trend for each MA
    trends = {}  # {period: "up" | "down" | "flat"}
    ma_values = {}  # {period: (current, previous)}

    for period in periods:
        ma_name = Indicator.MA(period)

        # Get current and previous MA values
        current_ma = history.indicator(ma_name, offset=0)
        previous_ma = history.indicator(ma_name, offset=lookback_bars)

        ma_values[period] = (current_ma, previous_ma)

        # Determine trend
        if current_ma > previous_ma:
            trends[period] = "up"
        elif current_ma < previous_ma:
            trends[period] = "down"
        else:
            trends[period] = "flat"

    # Check if all trends are the same (and not flat)
    trend_values = list(trends.values())
    unique_trends = set(trend_values)

    # All trending up
    if unique_trends == {"up"}:
        current_bar = history.current

        # Calculate average slope across all MAs
        slopes = []
        for _, (current, previous) in ma_values.items():
            if previous > 0:
                slope_pct = ((current / previous) - 1) * 100
                slopes.append(slope_pct)

        avg_slope = sum(slopes) / len(slopes) if slopes else 0

        return Signal(
            message=f"Strong uptrend: All {len(periods)} MAs trending up",
            severity="action",
            timestamp=current_bar.date,
            metadata={
                "direction": "up",
                "ma_periods": periods,
                "lookback_bars": lookback_bars,
                "avg_slope_pct": round(avg_slope, 4),
                "trends": {f"MA{p}": trends[p] for p in periods},
                "ma_values": {f"MA{p}": round(current, 2) for p, (current, _) in ma_values.items()},
            },
        )

    # All trending down
    if unique_trends == {"down"}:
        current_bar = history.current

        # Calculate average slope across all MAs
        slopes = []
        for _, (current, previous) in ma_values.items():
            if previous > 0:
                slope_pct = ((current / previous) - 1) * 100
                slopes.append(slope_pct)

        avg_slope = sum(slopes) / len(slopes) if slopes else 0

        return Signal(
            message=f"Strong downtrend: All {len(periods)} MAs trending down",
            severity="warning",
            timestamp=current_bar.date,
            metadata={
                "direction": "down",
                "ma_periods": periods,
                "lookback_bars": lookback_bars,
                "avg_slope_pct": round(avg_slope, 4),
                "trends": {f"MA{p}": trends[p] for p in periods},
                "ma_values": {f"MA{p}": round(current, 2) for p, (current, _) in ma_values.items()},
            },
        )

    # Mixed trends or all flat - no signal
    logger.debug(f"MAs not aligned: {trends}. No strong trend signal.")
    return None
