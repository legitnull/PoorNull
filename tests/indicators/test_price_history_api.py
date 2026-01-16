"""Tests for PriceHistory-based indicator API."""

import pandas as pd
import pytest

from poornull.data.models import PriceHistory
from poornull.indicators import with_ema, with_ma, with_ma_ema, with_macd, with_tomdemark


@pytest.fixture
def sample_price_history():
    """Create sample PriceHistory with 100 bars."""
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    df = pd.DataFrame(
        {
            "date": dates,
            "open": [100.0 + i * 0.5 for i in range(100)],
            "high": [102.0 + i * 0.5 for i in range(100)],
            "low": [98.0 + i * 0.5 for i in range(100)],
            "close": [101.0 + i * 0.5 for i in range(100)],
            "volume": [1000.0 + i * 10 for i in range(100)],
        }
    )
    return PriceHistory(df)


class TestWithMA:
    """Tests for with_ma function."""

    def test_with_ma_default_periods(self, sample_price_history):
        history = with_ma(sample_price_history)
        assert history.has_indicator("MA5")
        assert history.has_indicator("MA10")
        assert history.has_indicator("MA20")
        assert history.has_indicator("MA30")
        assert history.has_indicator("MA60")

    def test_with_ma_custom_periods(self, sample_price_history):
        history = with_ma(sample_price_history, periods=[5, 10, 250])
        assert history.has_indicator("MA5")
        assert history.has_indicator("MA10")
        assert history.has_indicator("MA250")
        assert not history.has_indicator("MA20")

    def test_with_ma_values(self, sample_price_history):
        history = with_ma(sample_price_history, periods=[5])
        ma5 = history.indicator("MA5")
        assert ma5 is not None
        assert ma5 > 0

    def test_with_ma_returns_price_history(self, sample_price_history):
        history = with_ma(sample_price_history)
        assert isinstance(history, PriceHistory)
        assert len(history) == len(sample_price_history)


class TestWithEMA:
    """Tests for with_ema function."""

    def test_with_ema_default_periods(self, sample_price_history):
        history = with_ema(sample_price_history)
        assert history.has_indicator("EMA5")
        assert history.has_indicator("EMA10")
        assert history.has_indicator("EMA20")
        assert history.has_indicator("EMA30")
        assert history.has_indicator("EMA60")

    def test_with_ema_custom_periods(self, sample_price_history):
        history = with_ema(sample_price_history, periods=[12, 26])
        assert history.has_indicator("EMA12")
        assert history.has_indicator("EMA26")
        assert not history.has_indicator("EMA5")

    def test_with_ema_values(self, sample_price_history):
        history = with_ema(sample_price_history, periods=[12])
        ema12 = history.indicator("EMA12")
        assert ema12 is not None
        assert ema12 > 0


class TestWithMAEMA:
    """Tests for with_ma_ema function."""

    def test_with_ma_ema_both(self, sample_price_history):
        history = with_ma_ema(sample_price_history)
        assert history.has_indicator("MA5")
        assert history.has_indicator("EMA5")

    def test_with_ma_ema_custom(self, sample_price_history):
        history = with_ma_ema(sample_price_history, ma_periods=[5, 10, 250], ema_periods=[12, 26])
        assert history.has_indicator("MA250")
        assert history.has_indicator("EMA12")


class TestWithMACD:
    """Tests for with_macd function."""

    def test_with_macd_default(self, sample_price_history):
        history = with_macd(sample_price_history)
        assert history.has_indicator("DIF")
        assert history.has_indicator("DEA")
        assert history.has_indicator("MACD")

    def test_with_macd_values(self, sample_price_history):
        history = with_macd(sample_price_history)
        dif = history.indicator("DIF")
        dea = history.indicator("DEA")
        macd = history.indicator("MACD")
        assert dif is not None
        assert dea is not None
        assert macd is not None

    def test_with_macd_custom_params(self, sample_price_history):
        history = with_macd(sample_price_history, fast=5, slow=10, signal=3)
        assert history.has_indicator("DIF")
        assert history.has_indicator("DEA")
        assert history.has_indicator("MACD")


class TestWithTomDeMark:
    """Tests for with_tomdemark function."""

    def test_with_tomdemark(self, sample_price_history):
        history = with_tomdemark(sample_price_history)
        assert history.has_indicator("TD_Phase")
        assert history.has_indicator("TD_Setup_Count")
        assert history.has_indicator("TD_Countdown_Count")
        assert history.has_indicator("TD_Phase_Name")

    def test_with_tomdemark_values(self, sample_price_history):
        history = with_tomdemark(sample_price_history)
        phase = history.indicator("TD_Phase")
        assert phase is not None
        assert phase >= 0


class TestChaining:
    """Tests for chaining multiple indicators."""

    def test_chain_ma_ema(self, sample_price_history):
        history = with_ma(sample_price_history, periods=[5, 10, 20])
        history = with_ema(history, periods=[12, 26])

        assert history.has_indicator("MA5")
        assert history.has_indicator("MA10")
        assert history.has_indicator("MA20")
        assert history.has_indicator("EMA12")
        assert history.has_indicator("EMA26")

    def test_chain_all_indicators(self, sample_price_history):
        history = sample_price_history
        history = with_ma(history, periods=[5, 10, 20, 30, 60, 250])
        history = with_ema(history, periods=[12, 26])
        history = with_macd(history)
        history = with_tomdemark(history)

        # Check all indicators present
        assert history.has_indicator("MA250")
        assert history.has_indicator("EMA12")
        assert history.has_indicator("DIF")
        assert history.has_indicator("TD_Phase")

    def test_chain_preserves_length(self, sample_price_history):
        original_len = len(sample_price_history)

        history = with_ma(sample_price_history, periods=[5, 10])
        history = with_ema(history, periods=[12, 26])
        history = with_macd(history)

        assert len(history) == original_len
