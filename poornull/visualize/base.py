"""Base utilities for visualization."""

import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

logger = logging.getLogger(__name__)


def setup_style(style: str = "darkgrid", figsize: tuple = (16, 10), fontsize: int = 10):
    """
    Setup matplotlib and seaborn style for charts.

    Args:
        style: Seaborn style (default: "darkgrid")
        figsize: Figure size tuple (default: (16, 10))
        fontsize: Base font size (default: 10)
    """
    sns.set_style(style)
    plt.rcParams["figure.figsize"] = figsize
    plt.rcParams["font.size"] = fontsize


def create_figure(nrows: int = 1, ncols: int = 1, height_ratios: list | None = None, sharex: bool = True):
    """
    Create a matplotlib figure with subplots.

    Args:
        nrows: Number of rows (default: 1)
        ncols: Number of columns (default: 1)
        height_ratios: Height ratios for subplots (default: None)
        sharex: Whether to share x-axis (default: True)

    Returns:
        Tuple of (figure, axes) where axes is always a list
    """
    if nrows == 1 and ncols == 1:
        fig, ax = plt.subplots(figsize=(16, 10))
        return fig, [ax]
    else:
        fig, axes = plt.subplots(nrows, ncols, height_ratios=height_ratios, sharex=sharex, figsize=(16, 10))
        # Convert to list format for consistent handling
        if nrows == 1:
            # Single row: axes is 1D array
            axes = [axes] if not isinstance(axes, np.ndarray) else axes.tolist()
        elif ncols == 1:
            # Single column: axes is 1D array
            if isinstance(axes, np.ndarray):
                axes = axes.tolist()
            elif not isinstance(axes, list):
                axes = [axes]
        else:
            # Multiple rows and columns: flatten to 1D list
            axes = axes.flatten().tolist()

        return fig, axes


def get_date_column(df: pd.DataFrame) -> str | None:
    """
    Find the date/timestamp column in a DataFrame.

    Args:
        df: DataFrame to search

    Returns:
        Column name if found, None otherwise
    """
    for col in df.columns:
        col_lower = str(col).lower()
        if "date" in col_lower or "timestamp" in col_lower or "日期" in str(col):
            return col
    return None


def format_date_axis(ax, date_col: str, df: pd.DataFrame):
    """
    Format date axis for better readability.

    Args:
        ax: Matplotlib axis
        date_col: Name of date column
        df: DataFrame with dates
    """
    import matplotlib.dates as mdates

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.step(ax.xaxis.get_majorticklabels(), rotation=45, ha="right")


def save_or_show(fig, save_path: str | None = None, dpi: int = 300, show: bool = True):
    """
    Save and/or show a figure.

    Args:
        fig: Matplotlib figure
        save_path: Path to save figure (default: None)
        dpi: Resolution for saved figure (default: 300)
        show: Whether to display the figure (default: True)
    """
    if save_path:
        fig.savefig(save_path, dpi=dpi, bbox_inches="tight")
        logger.info(f"Chart saved to {save_path}")

    if show:
        try:
            plt.show(block=False)
            logger.info("Chart displayed (close window to continue)")
        except Exception:
            logger.info("Chart saved (display not available in this environment)")
