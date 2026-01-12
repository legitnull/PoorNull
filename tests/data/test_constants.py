"""Tests for data constants."""

from poornull.data.constants import AKSHARE_COLUMN_MAPPING


class TestConstants:
    """Test constants module."""

    def test_column_mapping_exists(self):
        """Test that column mapping is defined."""
        assert AKSHARE_COLUMN_MAPPING is not None
        assert isinstance(AKSHARE_COLUMN_MAPPING, dict)
        assert len(AKSHARE_COLUMN_MAPPING) > 0

    def test_column_mapping_contains_expected_keys(self):
        """Test that column mapping contains expected Chinese keys."""
        expected_chinese_keys = ["日期", "收盘", "开盘", "最高", "最低", "成交量"]
        for key in expected_chinese_keys:
            assert key in AKSHARE_COLUMN_MAPPING

    def test_column_mapping_contains_expected_values(self):
        """Test that column mapping contains expected English values."""
        expected_english_values = ["date", "close", "open", "high", "low", "volume"]
        for value in expected_english_values:
            assert value in AKSHARE_COLUMN_MAPPING.values()

    def test_column_mapping_mappings(self):
        """Test specific column mappings."""
        assert AKSHARE_COLUMN_MAPPING["日期"] == "date"
        assert AKSHARE_COLUMN_MAPPING["收盘"] == "close"
        assert AKSHARE_COLUMN_MAPPING["开盘"] == "open"
        assert AKSHARE_COLUMN_MAPPING["最高"] == "high"
        assert AKSHARE_COLUMN_MAPPING["最低"] == "low"
        assert AKSHARE_COLUMN_MAPPING["成交量"] == "volume"
