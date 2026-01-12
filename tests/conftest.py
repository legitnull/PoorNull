"""Pytest configuration and shared fixtures."""

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_stock_data():
    """Create sample stock data for testing."""
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    # Create realistic price data with some trend
    np.random.seed(42)
    base_price = 100
    trend = np.linspace(0, 10, 100)
    noise = np.random.randn(100) * 2
    prices = base_price + trend + noise

    return pd.DataFrame(
        {
            "date": dates,
            "close": prices,
            "open": prices - 0.5,
            "high": prices + 1.0,
            "low": prices - 1.0,
            "volume": np.random.randint(1000000, 10000000, 100),
        }
    )
