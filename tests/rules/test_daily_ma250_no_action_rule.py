"""Tests for daily MA250 no-action rule."""

import logging

import pandas as pd
import pytest

from poornull.data.constants import Indicator
from poornull.data.models import PriceHistory
from poornull.rules.daily_ma250_no_action_rule import evaluate_daily_ma250_no_action


@pytest.fixture
def price_above_ma250():
    """Price above MA250."""
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=5),
            "open": [100.0, 101.0, 102.0, 103.0, 104.0],
            "high": [102.0, 103.0, 104.0, 105.0, 106.0],
            "low": [99.0, 100.0, 101.0, 102.0, 103.0],
            "close": [101.0, 102.0, 103.0, 104.0, 105.0],
            "volume": [1000.0] * 5,
            Indicator.MA(250): [95.0] * 5,
        }
    )


@pytest.fixture
def price_below_ma250():
    """Price below MA250."""
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=5),
            "open": [90.0, 91.0, 92.0, 93.0, 94.0],
            "high": [92.0, 93.0, 94.0, 95.0, 96.0],
            "low": [89.0, 90.0, 91.0, 92.0, 93.0],
            "close": [91.0, 92.0, 93.0, 94.0, 95.0],
            "volume": [1000.0] * 5,
            Indicator.ma(250): [100.0] * 5,
        }
    )


@pytest.fixture
def no_ma250():
    """DataFrame without MA250."""
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=5),
            "open": [100.0, 101.0, 102.0, 103.0, 104.0],
            "high": [102.0, 103.0, 104.0, 105.0, 106.0],
            "low": [99.0, 100.0, 101.0, 102.0, 103.0],
            "close": [101.0, 102.0, 103.0, 104.0, 105.0],
            "volume": [1000.0] * 5,
        }
    )


class TestDailyMA250NoActionRule:
    """Tests for MA250 no-action rule."""

    def test_price_above_ma250_no_signal(self, price_above_ma250):
        history = PriceHistory(price_above_ma250)
        signal = evaluate_daily_ma250_no_action(history)
        assert signal is None

    def test_price_below_ma250_returns_signal(self, price_below_ma250):
        history = PriceHistory(price_below_ma250)
        signal = evaluate_daily_ma250_no_action(history)
        assert signal is not None
        assert "MA250" in signal.message
        assert signal.severity == "warning"

    def test_signal_metadata(self, price_below_ma250):
        history = PriceHistory(price_below_ma250)
        signal = evaluate_daily_ma250_no_action(history)
        assert signal.metadata is not None
        assert "close" in signal.metadata
        assert "ma250" in signal.metadata
        assert "distance_pct" in signal.metadata
        assert signal.metadata["close"] == 95.0
        assert signal.metadata["ma250"] == 100.0

    def test_no_ma250_no_signal(self, no_ma250):
        history = PriceHistory(no_ma250)
        signal = evaluate_daily_ma250_no_action(history)
        assert signal is None

    def test_signal_timestamp(self, price_below_ma250):
        history = PriceHistory(price_below_ma250)
        signal = evaluate_daily_ma250_no_action(history)
        assert signal.timestamp is not None
        assert signal.timestamp == history.current.date

    def test_missing_ma250_logs_warning(self, no_ma250, caplog):
        """Test that missing MA250 logs a warning."""
        history = PriceHistory(no_ma250)

        with caplog.at_level(logging.WARNING):
            signal = evaluate_daily_ma250_no_action(history)

        assert signal is None
        assert "MA250 indicator not found" in caplog.text
        assert "with_ma(history, periods=[250])" in caplog.text
