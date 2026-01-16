"""Tests for MA trend alignment rule."""

import logging

import pandas as pd
import pytest

from poornull.data.constants import Indicator
from poornull.data.models import PriceHistory
from poornull.rules.ma_trend_alignment_rule import evaluate_ma_trend_alignment


@pytest.fixture
def trending_up_data():
    """All MAs trending up."""
    dates = pd.date_range("2024-01-01", periods=10, freq="D")

    # Create data where all MAs trend up
    df = pd.DataFrame(
        {
            "date": dates,
            "open": list(range(100, 110)),
            "high": list(range(102, 112)),
            "low": list(range(98, 108)),
            "close": list(range(100, 110)),
            "volume": [1000.0] * 10,
            Indicator.ma(5): list(range(100, 110)),  # Trending up
            Indicator.ma(10): list(range(95, 105)),  # Trending up
            Indicator.ma(20): list(range(90, 100)),  # Trending up
            Indicator.ma(30): list(range(85, 95)),  # Trending up
            Indicator.ma(60): list(range(80, 90)),  # Trending up
        }
    )
    return df


@pytest.fixture
def trending_down_data():
    """All MAs trending down."""
    dates = pd.date_range("2024-01-01", periods=10, freq="D")

    # Create data where all MAs trend down
    df = pd.DataFrame(
        {
            "date": dates,
            "open": list(range(110, 100, -1)),
            "high": list(range(112, 102, -1)),
            "low": list(range(108, 98, -1)),
            "close": list(range(110, 100, -1)),
            "volume": [1000.0] * 10,
            Indicator.ma(5): list(range(110, 100, -1)),  # Trending down
            Indicator.ma(10): list(range(115, 105, -1)),  # Trending down
            Indicator.ma(20): list(range(120, 110, -1)),  # Trending down
            Indicator.ma(30): list(range(125, 115, -1)),  # Trending down
            Indicator.ma(60): list(range(130, 120, -1)),  # Trending down
        }
    )
    return df


@pytest.fixture
def mixed_trend_data():
    """Mixed MA trends."""
    dates = pd.date_range("2024-01-01", periods=10, freq="D")

    # Some MAs up, some down
    df = pd.DataFrame(
        {
            "date": dates,
            "open": [100.0] * 10,
            "high": [102.0] * 10,
            "low": [98.0] * 10,
            "close": [100.0] * 10,
            "volume": [1000.0] * 10,
            Indicator.ma(5): list(range(100, 110)),  # Up
            Indicator.ma(10): list(range(100, 110)),  # Up
            Indicator.ma(20): list(range(110, 100, -1)),  # Down
            Indicator.ma(30): list(range(110, 100, -1)),  # Down
            Indicator.ma(60): [100.0] * 10,  # Flat
        }
    )
    return df


@pytest.fixture
def missing_ma_data():
    """Data missing some MAs."""
    dates = pd.date_range("2024-01-01", periods=10, freq="D")

    df = pd.DataFrame(
        {
            "date": dates,
            "open": list(range(100, 110)),
            "high": list(range(102, 112)),
            "low": list(range(98, 108)),
            "close": list(range(100, 110)),
            "volume": [1000.0] * 10,
            Indicator.ma(5): list(range(100, 110)),
            Indicator.ma(10): list(range(95, 105)),
            # Missing MA20, MA30, MA60
        }
    )
    return df


class TestMATrendAlignment:
    """Tests for MA trend alignment rule."""

    def test_all_mas_trending_up(self, trending_up_data):
        """Test signal when all MAs trending up."""
        history = PriceHistory(trending_up_data)
        signal = evaluate_ma_trend_alignment(history)

        assert signal is not None
        assert "uptrend" in signal.message.lower()
        assert signal.severity == "action"
        assert signal.metadata["direction"] == "up"
        assert signal.metadata["ma_periods"] == [5, 10, 20, 30, 60]
        assert signal.metadata["avg_slope_pct"] > 0

    def test_all_mas_trending_down(self, trending_down_data):
        """Test signal when all MAs trending down."""
        history = PriceHistory(trending_down_data)
        signal = evaluate_ma_trend_alignment(history)

        assert signal is not None
        assert "downtrend" in signal.message.lower()
        assert signal.severity == "warning"
        assert signal.metadata["direction"] == "down"
        assert signal.metadata["ma_periods"] == [5, 10, 20, 30, 60]
        assert signal.metadata["avg_slope_pct"] < 0

    def test_mixed_trends_no_signal(self, mixed_trend_data):
        """Test no signal when MAs have mixed trends."""
        history = PriceHistory(mixed_trend_data)
        signal = evaluate_ma_trend_alignment(history)

        assert signal is None

    def test_missing_mas_no_signal(self, missing_ma_data, caplog):
        """Test no signal when required MAs are missing."""
        history = PriceHistory(missing_ma_data)

        with caplog.at_level(logging.WARNING):
            signal = evaluate_ma_trend_alignment(history)

        assert signal is None
        assert "Required MA indicators not found" in caplog.text

    def test_custom_periods(self, trending_up_data):
        """Test with custom MA periods."""
        # Only check MA5 and MA10
        history = PriceHistory(trending_up_data)
        signal = evaluate_ma_trend_alignment(history, periods=[5, 10])

        assert signal is not None
        assert signal.metadata["ma_periods"] == [5, 10]

    def test_custom_lookback(self, trending_up_data):
        """Test with custom lookback period."""
        history = PriceHistory(trending_up_data)
        signal = evaluate_ma_trend_alignment(history, lookback_bars=2)

        assert signal is not None
        assert signal.metadata["lookback_bars"] == 2

    def test_insufficient_data(self):
        """Test with insufficient data points."""
        dates = pd.date_range("2024-01-01", periods=1, freq="D")
        df = pd.DataFrame(
            {
                "date": dates,
                "open": [100.0],
                "high": [102.0],
                "low": [98.0],
                "close": [100.0],
                "volume": [1000.0],
                Indicator.ma(5): [100.0],
            }
        )

        history = PriceHistory(df)
        signal = evaluate_ma_trend_alignment(history, periods=[5], lookback_bars=1)

        assert signal is None

    def test_signal_metadata_complete(self, trending_up_data):
        """Test that signal metadata is complete."""
        history = PriceHistory(trending_up_data)
        signal = evaluate_ma_trend_alignment(history)

        assert "direction" in signal.metadata
        assert "ma_periods" in signal.metadata
        assert "lookback_bars" in signal.metadata
        assert "avg_slope_pct" in signal.metadata
        assert "trends" in signal.metadata
        assert "ma_values" in signal.metadata

        # Check trends structure
        trends = signal.metadata["trends"]
        assert "MA5" in trends
        assert "MA10" in trends
        assert "MA20" in trends
        assert "MA30" in trends
        assert "MA60" in trends

    def test_signal_timestamp(self, trending_up_data):
        """Test that signal includes correct timestamp."""
        history = PriceHistory(trending_up_data)
        signal = evaluate_ma_trend_alignment(history)

        assert signal is not None
        assert signal.timestamp == history.current.date
