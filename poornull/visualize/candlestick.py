"""Candlestick chart visualization."""

import pandas as pd

from .base import get_date_column


def plot_candlesticks(
    ax,
    df: pd.DataFrame,
    date_col: str | None = None,
    open_col: str = "open",
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
    width: float = 0.6,
    up_color: str = "green",
    down_color: str = "red",
    alpha: float = 0.8,
):
    """
    Plot candlestick chart on given axis.

    Args:
        ax: Matplotlib axis to plot on
        df: DataFrame with OHLC data
        date_col: Name of date column (auto-detected if None)
        open_col: Name of open price column (default: "open")
        high_col: Name of high price column (default: "high")
        low_col: Name of low price column (default: "low")
        close_col: Name of close price column (default: "close")
        width: Width of candlesticks (default: 0.6)
        up_color: Color for up candles (default: "green")
        down_color: Color for down candles (default: "red")
        alpha: Transparency (default: 0.8)
    """
    if date_col is None:
        date_col = get_date_column(df)
        if date_col is None:
            raise ValueError("Could not find date column in DataFrame")

    # Convert dates to datetime for proper alignment with other indicators
    dates = pd.to_datetime(df[date_col])

    # Calculate width in days for candlestick rectangles
    if len(dates) > 1:
        # Use average time difference between dates
        time_diffs = dates.diff().dropna()
        if len(time_diffs) > 0:
            avg_diff = time_diffs.mean()
            # Convert width to timedelta (width is fraction of average period)
            width_timedelta = avg_diff * width
        else:
            width_timedelta = pd.Timedelta(days=1) * width
    else:
        width_timedelta = pd.Timedelta(days=1) * width

    # Plot wicks (high-low lines) and bodies
    for i, (_, row) in enumerate(df.iterrows()):
        date = dates.iloc[i]
        high = row[high_col]
        low = row[low_col]
        open_price = row[open_col]
        close_price = row[close_col]

        # Determine if up or down candle
        is_up = close_price >= open_price
        color = up_color if is_up else down_color

        # Draw wick (high-low line) using dates
        ax.plot([date, date], [low, high], color=color, linewidth=1, alpha=alpha, zorder=1)

        # Draw body (open-close rectangle) using bar chart approach for date compatibility
        body_low = min(open_price, close_price)
        body_high = max(open_price, close_price)
        body_height = body_high - body_low

        # Use bar chart for bodies (works better with date axes)
        if body_height > 0:
            if is_up:
                # Filled bar for up candle
                ax.bar(
                    date,
                    body_height,
                    bottom=body_low,
                    width=width_timedelta,
                    color=color,
                    edgecolor=color,
                    alpha=alpha,
                    zorder=2,
                )
            else:
                # Hollow bar for down candle
                ax.bar(
                    date,
                    body_height,
                    bottom=body_low,
                    width=width_timedelta,
                    color="white",
                    edgecolor=color,
                    linewidth=2,
                    alpha=alpha,
                    zorder=2,
                )
        else:
            # Doji (open == close) - draw horizontal line
            ax.plot(
                [date - width_timedelta / 2, date + width_timedelta / 2],
                [close_price, close_price],
                color=color,
                linewidth=2,
                alpha=alpha,
                zorder=2,
            )

    ax.set_ylabel("Price", fontsize=12, fontweight="bold")
    ax.grid(True, alpha=0.3)


def plot_price_line(
    ax,
    df: pd.DataFrame,
    date_col: str | None = None,
    price_col: str = "close",
    label: str = "Price",
    color: str = "black",
    linewidth: float = 1.5,
    alpha: float = 0.7,
):
    """
    Plot a simple price line (alternative to candlesticks).

    Args:
        ax: Matplotlib axis to plot on
        df: DataFrame with price data
        date_col: Name of date column (auto-detected if None)
        price_col: Name of price column (default: "close")
        label: Label for legend (default: "Price")
        color: Line color (default: "black")
        linewidth: Line width (default: 1.5)
        alpha: Transparency (default: 0.7)
    """
    if date_col is None:
        date_col = get_date_column(df)
        if date_col is None:
            raise ValueError("Could not find date column in DataFrame")

    dates = pd.to_datetime(df[date_col])
    ax.plot(dates, df[price_col], label=label, linewidth=linewidth, color=color, alpha=alpha)
    ax.set_ylabel("Price", fontsize=12, fontweight="bold")
    ax.grid(True, alpha=0.3)
