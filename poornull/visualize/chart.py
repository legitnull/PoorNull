"""High-level chart composition functions."""

import matplotlib.pyplot as plt
import pandas as pd

from .base import create_figure, format_date_axis, get_date_column, save_or_show, setup_style
from .candlestick import plot_candlesticks, plot_price_line
from .ma import plot_moving_averages
from .tomdemark import plot_tomdemark_counters, plot_tomdemark_sequential
from .trendline import plot_trendlines


def create_stock_chart(
    df: pd.DataFrame,
    chart_type: str = "line",
    show_ma: bool = True,
    show_trendlines: bool = False,
    show_tomdemark: bool = False,
    ma_periods: list[int] | None = None,
    title: str | None = None,
    save_path: str | None = None,
    show: bool = True,
) -> tuple:
    """
    Create a comprehensive stock chart with multiple indicators.

    Args:
        df: DataFrame with OHLC and indicator data
        chart_type: "line" or "candlestick" (default: "line")
        show_ma: Whether to show moving averages (default: True)
        show_trendlines: Whether to show trendlines (default: False)
        show_tomdemark: Whether to show TomDeMark Sequential (default: False)
        ma_periods: List of MA periods to show (default: [5, 10, 20, 30, 60])
        title: Chart title (default: None)
        save_path: Path to save chart (default: None)
        show: Whether to display chart (default: True)

    Returns:
        Tuple of (figure, axes)
    """
    setup_style()

    date_col = get_date_column(df)
    if date_col is None:
        raise ValueError("Could not find date column in DataFrame")

    # Determine number of subplots needed
    nrows = 1
    if show_tomdemark:
        nrows = 2  # Main chart + TD Sequential counters

    fig, axes = create_figure(nrows=nrows, ncols=1, height_ratios=[3, 1] if nrows == 2 else None)
    if nrows == 1:
        axes = [axes]

    ax_main = axes[0]

    # Plot price
    if chart_type == "candlestick":
        plot_candlesticks(ax_main, df, date_col=date_col)
    else:
        plot_price_line(ax_main, df, date_col=date_col, price_col="close")

    # Plot moving averages
    if show_ma:
        plot_moving_averages(ax_main, df, date_col=date_col, ma_periods=ma_periods)

    # Plot trendlines
    if show_trendlines:
        plot_trendlines(ax_main, df, date_col=date_col, method="linear")

    # Plot TomDeMark Sequential
    if show_tomdemark and "TD_Phase" in df.columns:
        plot_tomdemark_sequential(ax_main, df, date_col=date_col)

    # Set title
    if title:
        ax_main.set_title(title, fontsize=14, fontweight="bold")
    ax_main.legend(loc="best", fontsize=9)

    # Plot TD Sequential counters if needed
    if show_tomdemark and nrows == 2 and "TD_Setup_Count" in df.columns:
        ax_counters = axes[1]
        plot_tomdemark_counters(ax_counters, df, date_col=date_col)
        format_date_axis(ax_counters, date_col, df)
    else:
        format_date_axis(ax_main, date_col, df)

    plt.tight_layout()

    if save_path or show:
        save_or_show(fig, save_path=save_path, show=show)

    return fig, axes


def create_tomdemark_chart(
    df: pd.DataFrame,
    stock_code: str,
    start_date: str,
    end_date: str,
    save_path: str | None = None,
    show: bool = True,
) -> tuple:
    """
    Create a dedicated TomDeMark Sequential chart.

    Args:
        df: DataFrame with TD Sequential data
        stock_code: Stock code for title
        start_date: Start date string
        end_date: End date string
        save_path: Path to save chart (default: None)
        show: Whether to display chart (default: True)

    Returns:
        Tuple of (figure, axes)
    """
    setup_style()

    date_col = get_date_column(df)
    if date_col is None:
        raise ValueError("Could not find date column in DataFrame")

    fig, axes = create_figure(nrows=2, ncols=1, height_ratios=[3, 1])
    ax_main, ax_counters = axes[0], axes[1]

    # Plot price line
    plot_price_line(ax_main, df, date_col=date_col, price_col="close")

    # Plot TomDeMark Sequential
    plot_tomdemark_sequential(ax_main, df, date_col=date_col, show_annotations=True)

    # Set title
    ax_main.set_title(
        f"TomDeMark Sequential Indicator - {stock_code} ({start_date} to {end_date})",
        fontsize=14,
        fontweight="bold",
    )
    ax_main.legend(loc="best", fontsize=9)
    ax_main.grid(True, alpha=0.3)

    # Plot counters
    plot_tomdemark_counters(ax_counters, df, date_col=date_col)
    format_date_axis(ax_counters, date_col, df)

    plt.tight_layout()

    if save_path or show:
        save_or_show(fig, save_path=save_path, show=show)

    return fig, axes
