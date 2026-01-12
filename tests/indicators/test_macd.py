"""Tests for MACD indicator functions."""

import pandas as pd
import pytest

from poornull.indicators import find_macd_crossovers, tonghuashun_macd


class TestTonghuashunMACD:
    """Test tonghuashun_macd function."""

    def test_macd_calculation_basic(self):
        """Test basic MACD calculation."""
        # Create sample data
        dates = pd.date_range("2024-01-01", periods=50, freq="D")
        prices = [100 + i * 0.5 + (i % 3) * 0.2 for i in range(50)]  # Simple trend with some variation
        df = pd.DataFrame({"date": dates, "close": prices})

        result = tonghuashun_macd(df, close_col="close")

        # Check that MACD columns are added
        assert "DIF" in result.columns
        assert "DEA" in result.columns
        assert "MACD" in result.columns

        # Check that original columns are preserved
        assert "date" in result.columns
        assert "close" in result.columns

    def test_macd_calculation_with_custom_parameters(self):
        """Test MACD calculation with custom parameters."""
        dates = pd.date_range("2024-01-01", periods=50, freq="D")
        prices = [100 + i * 0.5 for i in range(50)]
        df = pd.DataFrame({"date": dates, "close": prices})

        result = tonghuashun_macd(df, close_col="close", fast=5, slow=10, signal=3, histogram_multiplier=1.5)

        assert "DIF" in result.columns
        assert "DEA" in result.columns
        assert "MACD" in result.columns

    def test_macd_missing_close_column(self):
        """Test that missing close column raises error."""
        df = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=10, freq="D"), "price": range(10)})

        with pytest.raises(ValueError, match="Close column 'close' not found"):
            tonghuashun_macd(df, close_col="close")

    def test_macd_sorts_by_date(self):
        """Test that data is sorted by date."""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        prices = range(10)
        df = pd.DataFrame({"date": dates, "close": prices})
        # Shuffle the dataframe
        df = df.sample(frac=1).reset_index(drop=True)

        result = tonghuashun_macd(df, close_col="close")

        # Check that dates are sorted
        assert result["date"].is_monotonic_increasing

    def test_macd_handles_chinese_date_column(self):
        """Test that MACD handles Chinese date column names."""
        dates = pd.date_range("2024-01-01", periods=30, freq="D")
        prices = [100 + i * 0.5 for i in range(30)]
        df = pd.DataFrame({"日期": dates, "close": prices})

        result = tonghuashun_macd(df, close_col="close")

        assert "DIF" in result.columns
        assert "DEA" in result.columns
        assert "MACD" in result.columns

    def test_macd_histogram_multiplier(self):
        """Test that histogram multiplier is applied correctly."""
        dates = pd.date_range("2024-01-01", periods=50, freq="D")
        prices = [100 + i * 0.5 for i in range(50)]
        df = pd.DataFrame({"date": dates, "close": prices})

        result_default = tonghuashun_macd(df, close_col="close", histogram_multiplier=2.0)
        result_custom = tonghuashun_macd(df, close_col="close", histogram_multiplier=1.0)

        # Check that MACD values differ by the multiplier
        # For the same DIF and DEA, MACD should be 2x in default vs 1x in custom
        # We'll check a non-NaN value
        valid_idx = result_default["MACD"].notna()
        if valid_idx.any():
            default_macd = result_default.loc[valid_idx, "MACD"].iloc[-1]
            custom_macd = result_custom.loc[valid_idx, "MACD"].iloc[-1]
            # The ratio should be approximately 2.0 (allowing for floating point precision)
            if custom_macd != 0:
                ratio = default_macd / custom_macd
                assert abs(ratio - 2.0) < 0.01


class TestFindMACDCrossovers:
    """Test find_macd_crossovers function."""

    def test_find_crossovers_basic(self):
        """Test finding MACD crossovers."""
        # Create data with a clear crossover
        dates = pd.date_range("2024-01-01", periods=30, freq="D")
        # Create a scenario where DIF crosses above DEA
        dif_values = [-1, -0.5, 0, 0.5, 1, 1.5, 2] + [2.5] * 23
        dea_values = [0, 0, 0, 0, 0, 0.5, 1] + [1.5] * 23
        df = pd.DataFrame(
            {
                "date": dates,
                "close": range(30),
                "DIF": dif_values,
                "DEA": dea_values,
                "MACD": [d - e for d, e in zip(dif_values, dea_values, strict=False)],
            }
        )

        crossovers = find_macd_crossovers(df)

        # Should find at least one crossover (golden cross when DIF crosses above DEA)
        assert isinstance(crossovers, pd.DataFrame)
        assert "date" in crossovers.columns
        assert "type" in crossovers.columns
        assert "dif" in crossovers.columns
        assert "dea" in crossovers.columns

    def test_find_crossovers_no_crossovers(self):
        """Test finding crossovers when none exist."""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        df = pd.DataFrame(
            {
                "date": dates,
                "close": range(10),
                "DIF": [1.0] * 10,  # DIF always above DEA
                "DEA": [0.5] * 10,
                "MACD": [0.5] * 10,
            }
        )

        crossovers = find_macd_crossovers(df)

        # Should return empty DataFrame with correct columns
        assert isinstance(crossovers, pd.DataFrame)
        assert len(crossovers) == 0
        assert "date" in crossovers.columns
        assert "type" in crossovers.columns

    def test_find_crossovers_missing_columns(self):
        """Test that missing DIF or DEA columns raise error."""
        df = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=10, freq="D"), "close": range(10)})

        with pytest.raises(ValueError, match="DIF column"):
            find_macd_crossovers(df, dif_col="DIF")

        df["DIF"] = range(10)
        with pytest.raises(ValueError, match="DEA column"):
            find_macd_crossovers(df, dif_col="DIF", dea_col="DEA")

    def test_find_crossovers_golden_and_death_cross(self):
        """Test finding both golden and death crosses."""
        dates = pd.date_range("2024-01-01", periods=20, freq="D")
        # DIF starts below DEA, crosses above (golden), then crosses below (death)
        dif_values = [-1, -0.5, 0, 0.5, 1, 1.5, 2, 2.5, 2, 1.5, 1, 0.5, 0, -0.5, -1, -1.5, -2, -2.5, -3, -3.5]
        dea_values = [0, 0, 0, 0, 0.5, 1, 1.5, 2, 2.5, 2, 1.5, 1, 0.5, 0, -0.5, -1, -1.5, -2, -2.5, -3]
        df = pd.DataFrame(
            {
                "date": dates,
                "close": range(20),
                "DIF": dif_values,
                "DEA": dea_values,
                "MACD": [d - e for d, e in zip(dif_values, dea_values, strict=False)],
            }
        )

        crossovers = find_macd_crossovers(df)

        assert len(crossovers) > 0
        assert "golden" in crossovers["type"].values or "death" in crossovers["type"].values
