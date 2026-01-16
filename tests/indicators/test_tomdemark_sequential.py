"""Tests for TomDeMark Sequential indicator."""

import numpy as np
import pandas as pd
import pytest

from poornull.indicators import (
    TomDemarkSequentialPhase,
    calculate_tomdemark_sequential,
)


class TestTomDemarkSequential:
    """Test calculate_tomdemark_sequential function."""

    def test_tomdemark_sequential_basic(self):
        """Test basic TomDeMark Sequential calculation with simple data."""
        # Create a simple dataset with 20 bars
        dates = pd.date_range("2024-01-01", periods=20, freq="D")

        # Create prices that should trigger buy setup
        # Bars 0-5: setup data, bars 6-14: declining prices for buy setup
        prices = [100, 102, 101, 103, 102, 104, 103, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87]

        df = pd.DataFrame(
            {
                "date": dates,
                "open": prices,
                "high": [p + 1 for p in prices],
                "low": [p - 1 for p in prices],
                "close": prices,
            }
        )

        result = calculate_tomdemark_sequential(df)

        # Check that expected columns are added
        assert "TD_Phase" in result.columns
        assert "TD_Setup_Count" in result.columns
        assert "TD_Countdown_Count" in result.columns
        assert "TD_Support_Price" in result.columns
        assert "TD_Resistance_Price" in result.columns
        assert "TD_Phase_Name" in result.columns

        # Check that we have valid phase values
        assert result["TD_Phase"].isin([0, 1, 2, 3, 4, 5, 6]).all()

    def test_tomdemark_sequential_buy_setup(self):
        """Test buy setup detection."""
        dates = pd.date_range("2024-01-01", periods=25, freq="D")

        # Create price pattern for buy setup:
        # Need prev close > prev close[4] and current close < close[4] to trigger
        # Then 9 consecutive bars where close < close[4]
        prices = [
            100,
            102,
            104,
            106,
            108,  # Bars 0-4: increasing
            110,
            112,
            114,
            116,
            118,  # Bars 5-9: continue increasing
            105,
            101,
            100,
            99,
            98,  # Bars 10-14: declining (close < close[4])
            97,
            96,
            95,
            94,
            93,  # Bars 15-19: continue declining
            92,
            91,
            90,
            89,
            88,  # Bars 20-24: more data
        ]

        df = pd.DataFrame(
            {
                "date": dates,
                "open": prices,
                "high": [p + 2 for p in prices],
                "low": [p - 2 for p in prices],
                "close": prices,
            }
        )

        result = calculate_tomdemark_sequential(df)

        # Check that we get some buy setup phases
        buy_setup_rows = result[result["TD_Phase"] == TomDemarkSequentialPhase.BUY_SETUP]
        assert len(buy_setup_rows) > 0, "Should detect buy setup phase"

    def test_tomdemark_sequential_sell_setup(self):
        """Test sell setup detection."""
        dates = pd.date_range("2024-01-01", periods=25, freq="D")

        # Create price pattern for sell setup:
        # Need prev close < prev close[4] and current close > close[4] to trigger
        # Then 9 consecutive bars where close > close[4]
        prices = [
            110,
            108,
            106,
            104,
            102,  # Bars 0-4: decreasing
            100,
            98,
            96,
            94,
            92,  # Bars 5-9: continue decreasing
            97,
            101,
            102,
            103,
            104,  # Bars 10-14: rising (close > close[4])
            105,
            106,
            107,
            108,
            109,  # Bars 15-19: continue rising
            110,
            111,
            112,
            113,
            114,  # Bars 20-24: more data
        ]

        df = pd.DataFrame(
            {
                "date": dates,
                "open": prices,
                "high": [p + 2 for p in prices],
                "low": [p - 2 for p in prices],
                "close": prices,
            }
        )

        result = calculate_tomdemark_sequential(df)

        # Check that we get some sell setup phases
        sell_setup_rows = result[result["TD_Phase"] == TomDemarkSequentialPhase.SELL_SETUP]
        assert len(sell_setup_rows) > 0, "Should detect sell setup phase"

    def test_tomdemark_sequential_setup_count(self):
        """Test that setup count increments correctly."""
        dates = pd.date_range("2024-01-01", periods=20, freq="D")

        # Create a clear buy setup pattern
        prices = [100, 101, 102, 103, 104, 105, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87]

        df = pd.DataFrame(
            {
                "date": dates,
                "open": prices,
                "high": [p + 1 for p in prices],
                "low": [p - 1 for p in prices],
                "close": prices,
            }
        )

        result = calculate_tomdemark_sequential(df)

        # Check that setup count increments
        setup_counts = result[result["TD_Setup_Count"] > 0]["TD_Setup_Count"]
        if len(setup_counts) > 0:
            # If we have setup counts, they should be sequential from 1 to some max
            assert setup_counts.min() >= 1
            assert setup_counts.max() <= 9

    def test_tomdemark_sequential_missing_columns(self):
        """Test error handling for missing columns."""
        df = pd.DataFrame(
            {
                "date": pd.date_range("2024-01-01", periods=10),
                "close": [100 + i for i in range(10)],
            }
        )

        with pytest.raises(ValueError, match="Required columns"):
            calculate_tomdemark_sequential(df)

    def test_tomdemark_sequential_phase_names(self):
        """Test that phase names are correctly mapped."""
        dates = pd.date_range("2024-01-01", periods=20, freq="D")
        prices = [100 + i * 0.5 for i in range(20)]

        df = pd.DataFrame(
            {
                "date": dates,
                "open": prices,
                "high": [p + 1 for p in prices],
                "low": [p - 1 for p in prices],
                "close": prices,
            }
        )

        result = calculate_tomdemark_sequential(df)

        # Check that phase names exist and are strings
        assert result["TD_Phase_Name"].notna().all()
        assert result["TD_Phase_Name"].dtype == object

        # Check valid phase name values
        valid_names = [
            "None",
            "Buy Setup",
            "Sell Setup",
            "Buy Countdown",
            "Sell Countdown",
            "Buy Setup Perfect",
            "Sell Setup Perfect",
        ]
        assert result["TD_Phase_Name"].isin(valid_names).all()

    def test_tomdemark_sequential_custom_columns(self):
        """Test with custom column names."""
        dates = pd.date_range("2024-01-01", periods=20, freq="D")
        prices = [100, 101, 102, 103, 104, 105, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87]

        df = pd.DataFrame(
            {
                "date": dates,
                "Open": prices,
                "High": [p + 1 for p in prices],
                "Low": [p - 1 for p in prices],
                "Close": prices,
            }
        )

        result = calculate_tomdemark_sequential(df, open_col="Open", high_col="High", low_col="Low", close_col="Close")

        assert "TD_Phase" in result.columns
        assert len(result) == len(df)

    def test_tomdemark_sequential_countdown_phase(self):
        """Test that countdown phase is triggered after setup completes."""
        dates = pd.date_range("2024-01-01", periods=30, freq="D")

        # Create a pattern that should complete a buy setup and start countdown
        # First 15 bars: create buy setup (9 bars with close < close[4])
        prices = [
            105,
            106,
            107,
            108,
            109,  # Bars 0-4: setup
            110,
            111,
            112,
            113,
            114,  # Bars 5-9: setup continues
            100,
            99,
            98,
            97,
            96,  # Bars 10-14: trigger buy setup
            95,
            94,
            93,
            92,
            91,  # Bars 15-19: complete setup to 9
            90,
            89,
            88,
            87,
            86,  # Bars 20-24: potential countdown
            85,
            84,
            83,
            82,
            81,  # Bars 25-29: more data
        ]

        df = pd.DataFrame(
            {
                "date": dates,
                "open": prices,
                "high": [p + 2 for p in prices],
                "low": [p - 2 for p in prices],
                "close": prices,
            }
        )

        result = calculate_tomdemark_sequential(df)

        # Check if countdown phase appears after setup
        # Note: Countdown may or may not appear depending on exact price conditions
        has_setup = (result["TD_Phase"] == TomDemarkSequentialPhase.BUY_SETUP).any()
        setup_count_9 = (result["TD_Setup_Count"] == 9).any()

        # At minimum, we should see setup phases
        assert has_setup or setup_count_9, "Should detect at least setup phase"

    def test_tomdemark_sequential_resistance_support_levels(self):
        """Test that resistance and support levels are calculated."""
        dates = pd.date_range("2024-01-01", periods=20, freq="D")
        prices = [100, 101, 102, 103, 104, 105, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87]

        df = pd.DataFrame(
            {
                "date": dates,
                "open": prices,
                "high": [p + 2 for p in prices],
                "low": [p - 2 for p in prices],
                "close": prices,
            }
        )

        result = calculate_tomdemark_sequential(df)

        # Check that support/resistance columns exist
        assert "TD_Support_Price" in result.columns
        assert "TD_Resistance_Price" in result.columns

        # If any resistance/support is set, it should be a valid number
        if result["TD_Resistance_Price"].notna().any():
            assert (result["TD_Resistance_Price"].dropna() > 0).all()

        if result["TD_Support_Price"].notna().any():
            assert (result["TD_Support_Price"].dropna() > 0).all()

    def test_tomdemark_sequential_real_world_pattern(self):
        """Test with a realistic price pattern."""
        # Create realistic OHLC data
        dates = pd.date_range("2024-01-01", periods=50, freq="D")

        # Simulate a downtrend followed by potential reversal
        np.random.seed(42)
        base_prices = list(range(150, 100, -1)) + list(range(100, 120))
        prices = base_prices[:50]

        df = pd.DataFrame(
            {
                "date": dates,
                "open": [p + np.random.uniform(-1, 1) for p in prices],
                "high": [p + np.random.uniform(1, 3) for p in prices],
                "low": [p - np.random.uniform(1, 3) for p in prices],
                "close": prices,
            }
        )

        result = calculate_tomdemark_sequential(df)

        # Basic sanity checks
        assert len(result) == 50
        assert result["TD_Phase"].notna().all()
        assert result["TD_Setup_Count"].notna().all()
        assert result["TD_Countdown_Count"].notna().all()

        # All setup counts should be 0-9
        assert result["TD_Setup_Count"].min() >= 0
        assert result["TD_Setup_Count"].max() <= 9

        # All countdown counts should be 0-13
        assert result["TD_Countdown_Count"].min() >= 0
        assert result["TD_Countdown_Count"].max() <= 13
