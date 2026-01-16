"""Visualization module for stock charts and technical indicators."""

from .base import create_figure, format_date_axis, get_date_column, save_or_show, setup_style
from .candlestick import plot_candlesticks, plot_price_line
from .chart import create_stock_chart, create_tomdemark_chart
from .ma import plot_ma_crossovers, plot_moving_averages
from .tomdemark import plot_tomdemark_counters, plot_tomdemark_sequential
from .trendline import (
    plot_support_resistance_levels,
    plot_trendlines,
)

__all__ = [
    # Base utilities
    "create_figure",
    "get_date_column",
    "setup_style",
    "format_date_axis",
    "save_or_show",
    # Candlestick
    "plot_candlesticks",
    "plot_price_line",
    # Moving Averages
    "plot_moving_averages",
    "plot_ma_crossovers",
    # Trendlines
    "plot_trendlines",
    "plot_support_resistance_levels",
    # TomDeMark Sequential
    "plot_tomdemark_sequential",
    "plot_tomdemark_counters",
    # High-level chart composition
    "create_stock_chart",
    "create_tomdemark_chart",
]
