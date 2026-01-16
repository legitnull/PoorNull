"""Moving Average visualization."""

import pandas as pd

from .base import get_date_column


def plot_moving_averages(
    ax,
    df: pd.DataFrame,
    date_col: str | None = None,
    ma_periods: list[int] | None = None,
    ema_periods: list[int] | None = None,
    colors: dict | None = None,
    linewidth: float = 1.5,
    alpha: float = 0.8,
):
    """
    Plot moving averages on given axis.

    Args:
        ax: Matplotlib axis to plot on
        df: DataFrame with MA/EMA columns
        date_col: Name of date column (auto-detected if None)
        ma_periods: List of MA periods to plot (default: [5, 10, 20, 30, 60])
        ema_periods: List of EMA periods to plot (default: None, plots all found)
        colors: Dict mapping period to color (default: None, uses default colors)
        linewidth: Line width (default: 1.5)
        alpha: Transparency (default: 0.8)
    """
    if date_col is None:
        date_col = get_date_column(df)
        if date_col is None:
            raise ValueError("Could not find date column in DataFrame")

    if ma_periods is None:
        # Auto-detect MA columns
        ma_cols = [col for col in df.columns if col.startswith("MA") and col[2:].isdigit()]
        ma_periods = [int(col[2:]) for col in ma_cols]
        ma_periods.sort()

    if ma_periods is None:
        ma_periods = [5, 10, 20, 30, 60]

    dates = pd.to_datetime(df[date_col])

    # Default colors for common periods
    default_colors = {
        5: "blue",
        10: "orange",
        20: "purple",
        30: "brown",
        60: "pink",
        120: "gray",
        250: "cyan",
    }

    # Plot MA lines
    for period in ma_periods:
        ma_col = f"MA{period}"
        if ma_col in df.columns:
            color = colors.get(period) if colors and period in colors else default_colors.get(period, "gray")
            ax.plot(
                dates,
                df[ma_col],
                label=f"MA{period}",
                linewidth=linewidth,
                color=color,
                alpha=alpha,
                linestyle="-",
            )

    # Plot EMA lines if requested
    if ema_periods is not None:
        for period in ema_periods:
            ema_col = f"EMA{period}"
            if ema_col in df.columns:
                color = (
                    colors.get(f"EMA{period}")
                    if colors and f"EMA{period}" in colors
                    else default_colors.get(period, "gray")
                )
                ax.plot(
                    dates,
                    df[ema_col],
                    label=f"EMA{period}",
                    linewidth=linewidth,
                    color=color,
                    alpha=alpha,
                    linestyle="--",
                )

    ax.legend(loc="best", fontsize=9)


def plot_ma_crossovers(
    ax,
    df: pd.DataFrame,
    date_col: str | None = None,
    ma1_col: str = "MA20",
    ma2_col: str = "MA60",
    up_color: str = "green",
    down_color: str = "red",
    marker_size: int = 100,
):
    """
    Plot MA crossover points on given axis.

    Args:
        ax: Matplotlib axis to plot on
        df: DataFrame with MA columns
        date_col: Name of date column (auto-detected if None)
        ma1_col: First MA column name (default: "MA20")
        ma2_col: Second MA column name (default: "MA60")
        up_color: Color for golden cross (default: "green")
        down_color: Color for death cross (default: "red")
        marker_size: Size of markers (default: 100)
    """
    if date_col is None:
        date_col = get_date_column(df)
        if date_col is None:
            raise ValueError("Could not find date column in DataFrame")

    if ma1_col not in df.columns or ma2_col not in df.columns:
        return  # No data to plot

    # Find crossovers
    df = df.copy()
    df["ma1_above"] = df[ma1_col] > df[ma2_col]
    df["crossover"] = df["ma1_above"] != df["ma1_above"].shift(1)

    # Plot golden crosses (ma1 crosses above ma2)
    golden_crosses = df[(df["crossover"]) & (df["ma1_above"])]
    if not golden_crosses.empty:
        ax.scatter(
            golden_crosses[date_col],
            golden_crosses[ma1_col],
            color=up_color,
            marker="^",
            s=marker_size,
            label="Golden Cross",
            zorder=5,
        )

    # Plot death crosses (ma1 crosses below ma2)
    death_crosses = df[(df["crossover"]) & (~df["ma1_above"])]
    if not death_crosses.empty:
        ax.scatter(
            death_crosses[date_col],
            death_crosses[ma1_col],
            color=down_color,
            marker="v",
            s=marker_size,
            label="Death Cross",
            zorder=5,
        )
