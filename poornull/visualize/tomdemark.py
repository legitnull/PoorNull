"""TomDeMark Sequential indicator visualization."""

import pandas as pd

from poornull.indicators import TomDemarkSequentialPhase

from .base import get_date_column


def plot_tomdemark_sequential(
    ax,
    df: pd.DataFrame,
    date_col: str | None = None,
    close_col: str = "close",
    setup_marker_size: int = 100,
    countdown_marker_size: int = 50,
    show_annotations: bool = True,
):
    """
    Plot TomDeMark Sequential phases on given axis.

    Args:
        ax: Matplotlib axis to plot on
        df: DataFrame with TD Sequential columns
        date_col: Name of date column (auto-detected if None)
        close_col: Name of close price column (default: "close")
        setup_marker_size: Size of setup markers (default: 100)
        countdown_marker_size: Size of countdown markers (default: 50)
        show_annotations: Whether to show annotations for completed phases (default: True)
    """
    if date_col is None:
        date_col = get_date_column(df)
        if date_col is None:
            raise ValueError("Could not find date column in DataFrame")

    # Highlight Buy Setup phases
    buy_setup_mask = df["TD_Phase"].isin(
        [TomDemarkSequentialPhase.BUY_SETUP, TomDemarkSequentialPhase.BUY_SETUP_PERFECT]
    )
    if buy_setup_mask.any():
        buy_setup_data = df[buy_setup_mask]
        ax.scatter(
            buy_setup_data[date_col],
            buy_setup_data[close_col],
            color="green",
            marker="^",
            s=setup_marker_size,
            label="Buy Setup",
            alpha=0.7,
            zorder=5,
        )

    # Highlight Sell Setup phases
    sell_setup_mask = df["TD_Phase"].isin(
        [TomDemarkSequentialPhase.SELL_SETUP, TomDemarkSequentialPhase.SELL_SETUP_PERFECT]
    )
    if sell_setup_mask.any():
        sell_setup_data = df[sell_setup_mask]
        ax.scatter(
            sell_setup_data[date_col],
            sell_setup_data[close_col],
            color="red",
            marker="v",
            s=setup_marker_size,
            label="Sell Setup",
            alpha=0.7,
            zorder=5,
        )

    # Highlight Buy Countdown
    buy_countdown_mask = df["TD_Phase"] == TomDemarkSequentialPhase.BUY_COUNTDOWN
    if buy_countdown_mask.any():
        buy_countdown_data = df[buy_countdown_mask]
        ax.scatter(
            buy_countdown_data[date_col],
            buy_countdown_data[close_col],
            color="lightgreen",
            marker="o",
            s=countdown_marker_size,
            label="Buy Countdown",
            alpha=0.5,
            zorder=4,
        )

    # Highlight Sell Countdown
    sell_countdown_mask = df["TD_Phase"] == TomDemarkSequentialPhase.SELL_COUNTDOWN
    if sell_countdown_mask.any():
        sell_countdown_data = df[sell_countdown_mask]
        ax.scatter(
            sell_countdown_data[date_col],
            sell_countdown_data[close_col],
            color="lightcoral",
            marker="o",
            s=countdown_marker_size,
            label="Sell Countdown",
            alpha=0.5,
            zorder=4,
        )

    # Plot TDST Support/Resistance levels
    resistance_mask = df["TD_Resistance_Price"].notna()
    if resistance_mask.any():
        resistance_data = df[resistance_mask]
        for _, row in resistance_data.iterrows():
            ax.axhline(
                y=row["TD_Resistance_Price"],
                color="red",
                linestyle="--",
                alpha=0.3,
                linewidth=1,
            )
        # Add label for first resistance
        first_resistance = df[resistance_mask]["TD_Resistance_Price"].iloc[0]
        ax.axhline(
            y=first_resistance,
            color="red",
            linestyle="--",
            alpha=0.5,
            linewidth=1.5,
            label=f"TDST Resistance: {first_resistance:.2f}",
        )

    support_mask = df["TD_Support_Price"].notna()
    if support_mask.any():
        support_data = df[support_mask]
        for _, row in support_data.iterrows():
            ax.axhline(
                y=row["TD_Support_Price"],
                color="green",
                linestyle="--",
                alpha=0.3,
                linewidth=1,
            )
        # Add label for first support
        first_support = df[support_mask]["TD_Support_Price"].iloc[0]
        ax.axhline(
            y=first_support,
            color="green",
            linestyle="--",
            alpha=0.5,
            linewidth=1.5,
            label=f"TDST Support: {first_support:.2f}",
        )

    # Annotate completed setups (count = 9)
    if show_annotations:
        completed_setups = df[df["TD_Setup_Count"] == 9]
        for _, row in completed_setups.iterrows():
            phase_name = row["TD_Phase_Name"]
            if "Buy" in phase_name:
                ax.annotate(
                    "Buy Setup\nComplete",
                    xy=(row[date_col], row[close_col]),
                    xytext=(10, 20),
                    textcoords="offset points",
                    fontsize=8,
                    bbox={"boxstyle": "round,pad=0.3", "facecolor": "lightgreen", "alpha": 0.7},
                    arrowprops={"arrowstyle": "->", "connectionstyle": "arc3,rad=0", "color": "green"},
                )
            elif "Sell" in phase_name:
                ax.annotate(
                    "Sell Setup\nComplete",
                    xy=(row[date_col], row[close_col]),
                    xytext=(10, -30),
                    textcoords="offset points",
                    fontsize=8,
                    bbox={"boxstyle": "round,pad=0.3", "facecolor": "lightcoral", "alpha": 0.7},
                    arrowprops={"arrowstyle": "->", "connectionstyle": "arc3,rad=0", "color": "red"},
                )

        # Annotate completed countdowns (count = 13)
        completed_countdowns = df[df["TD_Countdown_Count"] == 13]
        for _, row in completed_countdowns.iterrows():
            phase_name = row["TD_Phase_Name"]
            if "Buy" in phase_name:
                ax.annotate(
                    "Buy Countdown\nComplete!",
                    xy=(row[date_col], row[close_col]),
                    xytext=(10, 30),
                    textcoords="offset points",
                    fontsize=9,
                    fontweight="bold",
                    bbox={"boxstyle": "round,pad=0.5", "facecolor": "green", "alpha": 0.8, "edgecolor": "darkgreen"},
                    arrowprops={"arrowstyle": "->", "connectionstyle": "arc3,rad=0", "color": "darkgreen", "lw": 2},
                )
            elif "Sell" in phase_name:
                ax.annotate(
                    "Sell Countdown\nComplete!",
                    xy=(row[date_col], row[close_col]),
                    xytext=(10, -40),
                    textcoords="offset points",
                    fontsize=9,
                    fontweight="bold",
                    bbox={"boxstyle": "round,pad=0.5", "facecolor": "red", "alpha": 0.8, "edgecolor": "darkred"},
                    arrowprops={"arrowstyle": "->", "connectionstyle": "arc3,rad=0", "color": "darkred", "lw": 2},
                )


def plot_tomdemark_counters(ax, df: pd.DataFrame, date_col: str | None = None):
    """
    Plot TD Sequential setup and countdown counters.

    Args:
        ax: Matplotlib axis to plot on
        df: DataFrame with TD Sequential columns
        date_col: Name of date column (auto-detected if None)
    """
    if date_col is None:
        date_col = get_date_column(df)
        if date_col is None:
            raise ValueError("Could not find date column in DataFrame")

    dates = pd.to_datetime(df[date_col])

    ax.bar(
        dates,
        df["TD_Setup_Count"],
        label="Setup Count",
        color="blue",
        alpha=0.6,
        width=1,
    )
    ax.bar(
        dates,
        df["TD_Countdown_Count"],
        label="Countdown Count",
        color="orange",
        alpha=0.6,
        width=1,
    )
    ax.axhline(y=9, color="blue", linestyle=":", alpha=0.5, label="Setup Target (9)")
    ax.axhline(y=13, color="orange", linestyle=":", alpha=0.5, label="Countdown Target (13)")
    ax.set_ylabel("Count", fontsize=10, fontweight="bold")
    ax.set_ylim(0, 15)
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)
