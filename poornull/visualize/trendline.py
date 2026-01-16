"""Trendline visualization."""

import numpy as np
import pandas as pd
from scipy import stats

from .base import get_date_column


def plot_trendlines(
    ax,
    df: pd.DataFrame,
    date_col: str | None = None,
    price_col: str = "close",
    method: str = "linear",
    lookback: int | None = None,
    color: str = "blue",
    linestyle: str = "--",
    linewidth: float = 1.5,
    alpha: float = 0.6,
    label: str = "Trendline",
):
    """
    Plot trendlines on given axis.

    Args:
        ax: Matplotlib axis to plot on
        df: DataFrame with price data
        date_col: Name of date column (auto-detected if None)
        price_col: Name of price column (default: "close")
        method: Trendline method - "linear" or "support_resistance" (default: "linear")
        lookback: Number of periods to use for trendline (default: None, uses all data)
        color: Line color (default: "blue")
        linestyle: Line style (default: "--")
        linewidth: Line width (default: 1.5)
        alpha: Transparency (default: 0.6)
        label: Label for legend (default: "Trendline")
    """
    if date_col is None:
        date_col = get_date_column(df)
        if date_col is None:
            raise ValueError("Could not find date column in DataFrame")

    dates = pd.to_datetime(df[date_col])

    # Use subset if lookback specified
    if lookback is not None and lookback < len(df):
        df_subset = df.tail(lookback).copy()
        dates_subset = dates.tail(lookback)
    else:
        df_subset = df.copy()
        dates_subset = dates

    if method == "linear":
        # Simple linear regression trendline
        x_numeric = np.arange(len(df_subset))
        y = df_subset[price_col].values

        # Remove NaN values
        mask = ~np.isnan(y)
        if not mask.any():
            return

        x_numeric = x_numeric[mask]
        y = y[mask]

        if len(x_numeric) < 2:
            return

        # Calculate linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x_numeric, y)

        # Generate trendline points
        x_trend = np.arange(len(df_subset))
        y_trend = slope * x_trend + intercept

        # Convert back to dates for plotting
        ax.plot(
            dates_subset,
            y_trend,
            color=color,
            linestyle=linestyle,
            linewidth=linewidth,
            alpha=alpha,
            label=f"{label} (R²={r_value**2:.3f})",
        )

    elif method == "support_resistance":
        # Plot support and resistance levels
        # Support: lowest lows in rolling window
        # Resistance: highest highs in rolling window
        window = min(20, len(df_subset) // 4)

        if window < 2:
            return

        # Calculate support (local minima)
        rolling_min = df_subset[price_col].rolling(window=window, center=True).min()
        support_levels = df_subset[df_subset[price_col] == rolling_min]

        # Calculate resistance (local maxima)
        rolling_max = df_subset[price_col].rolling(window=window, center=True).max()
        resistance_levels = df_subset[df_subset[price_col] == rolling_max]

        # Plot support
        if not support_levels.empty:
            ax.scatter(
                support_levels[date_col],
                support_levels[price_col],
                color="green",
                marker="_",
                s=200,
                alpha=0.7,
                label="Support",
                zorder=5,
            )
            # Draw horizontal line at average support
            avg_support = support_levels[price_col].mean()
            ax.axhline(
                y=avg_support,
                color="green",
                linestyle="--",
                alpha=0.5,
                linewidth=1,
                label=f"Avg Support: {avg_support:.2f}",
            )

        # Plot resistance
        if not resistance_levels.empty:
            ax.scatter(
                resistance_levels[date_col],
                resistance_levels[price_col],
                color="red",
                marker="_",
                s=200,
                alpha=0.7,
                label="Resistance",
                zorder=5,
            )
            # Draw horizontal line at average resistance
            avg_resistance = resistance_levels[price_col].mean()
            ax.axhline(
                y=avg_resistance,
                color="red",
                linestyle="--",
                alpha=0.5,
                linewidth=1,
                label=f"Avg Resistance: {avg_resistance:.2f}",
            )


def plot_support_resistance_levels(
    ax,
    support_levels: list[float],
    resistance_levels: list[float],
    support_color: str = "green",
    resistance_color: str = "red",
    linestyle: str = "--",
    linewidth: float = 1,
    alpha: float = 0.5,
):
    """
    Plot support and resistance levels as horizontal lines.

    Args:
        ax: Matplotlib axis to plot on
        support_levels: List of support price levels
        resistance_levels: List of resistance price levels
        support_color: Color for support lines (default: "green")
        resistance_color: Color for resistance lines (default: "red")
        linestyle: Line style (default: "--")
        linewidth: Line width (default: 1)
        alpha: Transparency (default: 0.5)
    """
    for level in support_levels:
        ax.axhline(y=level, color=support_color, linestyle=linestyle, linewidth=linewidth, alpha=alpha)

    for level in resistance_levels:
        ax.axhline(y=level, color=resistance_color, linestyle=linestyle, linewidth=linewidth, alpha=alpha)
