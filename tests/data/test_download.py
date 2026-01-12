"""Tests for data download functions."""

from unittest.mock import Mock, patch

import pytest

from poornull.data import (
    Period,
    download_daily,
    download_monthly,
    download_quarterly,
    download_stock_data,
    download_weekly,
)


class TestPeriod:
    """Test Period enum."""

    def test_period_values(self):
        """Test that Period enum has correct values."""
        assert Period.DAILY.value == "daily"
        assert Period.WEEKLY.value == "weekly"
        assert Period.MONTHLY.value == "monthly"
        assert Period.QUARTERLY.value == "quarterly"


class TestDownloadStockData:
    """Test download_stock_data function."""

    @patch("poornull.data.download.ak.stock_zh_a_hist")
    def test_download_daily_data(self, mock_akshare):
        """Test downloading daily stock data."""
        # Mock akshare response
        mock_df = Mock()
        mock_df.empty = False
        mock_df.columns = ["日期", "收盘", "开盘", "最高", "最低", "成交量"]
        mock_df.rename.return_value = mock_df
        mock_df.sort_values.return_value = mock_df
        mock_akshare.return_value = mock_df

        result = download_stock_data("600036", "20240101", "20241231", period=Period.DAILY)

        # Verify akshare was called with correct parameters
        mock_akshare.assert_called_once_with(
            symbol="600036",
            period="daily",
            start_date="20240101",
            end_date="20241231",
            adjust="",
        )
        assert result is not None

    @patch("poornull.data.download.ak.stock_zh_a_hist")
    def test_download_weekly_data(self, mock_akshare):
        """Test downloading weekly stock data."""
        mock_df = Mock()
        mock_df.empty = False
        mock_df.columns = ["日期", "收盘", "开盘", "最高", "最低", "成交量"]
        mock_df.rename.return_value = mock_df
        mock_df.sort_values.return_value = mock_df
        mock_akshare.return_value = mock_df

        result = download_stock_data("600036", "20240101", "20241231", period=Period.WEEKLY)

        mock_akshare.assert_called_once_with(
            symbol="600036",
            period="weekly",
            start_date="20240101",
            end_date="20241231",
            adjust="",
        )
        assert result is not None

    @patch("poornull.data.download.ak.stock_zh_a_hist")
    def test_download_monthly_data(self, mock_akshare):
        """Test downloading monthly stock data."""
        mock_df = Mock()
        mock_df.empty = False
        mock_df.columns = ["日期", "收盘", "开盘", "最高", "最低", "成交量"]
        mock_df.rename.return_value = mock_df
        mock_df.sort_values.return_value = mock_df
        mock_akshare.return_value = mock_df

        result = download_stock_data("600036", "20240101", "20241231", period=Period.MONTHLY)

        mock_akshare.assert_called_once_with(
            symbol="600036",
            period="monthly",
            start_date="20240101",
            end_date="20241231",
            adjust="",
        )
        assert result is not None

    @patch("poornull.data.download.ak.stock_zh_a_hist")
    def test_download_quarterly_data(self, mock_akshare):
        """Test downloading quarterly stock data."""
        mock_df = Mock()
        mock_df.empty = False
        mock_df.columns = ["日期", "收盘", "开盘", "最高", "最低", "成交量"]
        mock_df.rename.return_value = mock_df
        mock_df.sort_values.return_value = mock_df
        mock_akshare.return_value = mock_df

        result = download_stock_data("600036", "20240101", "20241231", period=Period.QUARTERLY)

        mock_akshare.assert_called_once_with(
            symbol="600036",
            period="quarterly",
            start_date="20240101",
            end_date="20241231",
            adjust="",
        )
        assert result is not None

    @patch("poornull.data.download.ak.stock_zh_a_hist")
    def test_empty_data_raises_error(self, mock_akshare):
        """Test that empty data raises ValueError."""
        mock_df = Mock()
        mock_df.empty = True
        mock_akshare.return_value = mock_df

        with pytest.raises(ValueError, match="No data found for stock"):
            download_stock_data("600036", "20240101", "20241231", period=Period.DAILY)

    @patch("poornull.data.download.ak.stock_zh_a_hist")
    def test_adjust_parameter(self, mock_akshare):
        """Test that adjust parameter is passed correctly."""
        mock_df = Mock()
        mock_df.empty = False
        mock_df.columns = ["日期", "收盘"]
        mock_df.rename.return_value = mock_df
        mock_df.sort_values.return_value = mock_df
        mock_akshare.return_value = mock_df

        download_stock_data("600036", "20240101", "20241231", period=Period.DAILY, adjust="qfq")

        mock_akshare.assert_called_once_with(
            symbol="600036",
            period="daily",
            start_date="20240101",
            end_date="20241231",
            adjust="qfq",
        )


class TestConvenienceWrappers:
    """Test convenience wrapper functions."""

    @patch("poornull.data.download.download_stock_data")
    def test_download_daily_wrapper(self, mock_download):
        """Test download_daily convenience wrapper."""
        mock_download.return_value = Mock()
        download_daily("600036", "20240101", "20241231")
        mock_download.assert_called_once_with("600036", "20240101", "20241231", period=Period.DAILY, adjust="")

    @patch("poornull.data.download.download_stock_data")
    def test_download_weekly_wrapper(self, mock_download):
        """Test download_weekly convenience wrapper."""
        mock_download.return_value = Mock()
        download_weekly("600036", "20240101", "20241231")
        mock_download.assert_called_once_with("600036", "20240101", "20241231", period=Period.WEEKLY, adjust="")

    @patch("poornull.data.download.download_stock_data")
    def test_download_monthly_wrapper(self, mock_download):
        """Test download_monthly convenience wrapper."""
        mock_download.return_value = Mock()
        download_monthly("600036", "20240101", "20241231")
        mock_download.assert_called_once_with("600036", "20240101", "20241231", period=Period.MONTHLY, adjust="")

    @patch("poornull.data.download.download_stock_data")
    def test_download_quarterly_wrapper(self, mock_download):
        """Test download_quarterly convenience wrapper."""
        mock_download.return_value = Mock()
        download_quarterly("600036", "20240101", "20241231")
        mock_download.assert_called_once_with("600036", "20240101", "20241231", period=Period.QUARTERLY, adjust="")
