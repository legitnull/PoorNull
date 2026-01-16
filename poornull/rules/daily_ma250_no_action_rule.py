"""Rule: No action when daily close is below MA250."""

import logging

from poornull.data.constants import Indicator
from poornull.data.models import PriceHistory, Signal

logger = logging.getLogger(__name__)


def evaluate_daily_ma250_no_action(history: PriceHistory) -> Signal | None:
    """
    Evaluate if daily close is below MA250.

    Args:
        history: Price history with MA250 computed

    Returns:
        Signal if rule triggered, None otherwise
    """
    if not history.has_indicator(Indicator.ma(250)):
        logger.warning(
            "MA250 indicator not found in price history. "
            "Rule 'daily_ma250_no_action' cannot be evaluated. "
            "Add MA250 using: history = with_ma(history, periods=[250])"
        )
        return None

    if history.is_below(Indicator.ma(250), bars=1):
        ma250 = history.indicator(Indicator.ma(250))
        current_bar = history.current

        return Signal(
            message="Daily close is below MA250 — no further action should be taken.",
            severity="warning",
            timestamp=current_bar.date,
            metadata={
                "close": current_bar.close,
                "ma250": ma250,
                "distance_pct": ((current_bar.close / ma250) - 1) * 100 if ma250 else None,
            },
        )

    return None
