"""
TomDeMark Sequential (TD Sequential) indicator.

This indicator identifies potential trend exhaustion points using Tom DeMark's Sequential methodology.
Implementation based on QuantConnect's Lean engine.

References:
- https://demark.com/sequential-indicator/
- https://practicaltechnicalanalysis.blogspot.com/2013/01/tom-demark-sequential.html
- https://medium.com/traderlands-blog/tds-td-sequential-indicator-2023-f8675bc5d14
"""

from enum import IntEnum

import numpy as np
import pandas as pd

from poornull.data.models import PriceHistory


class TomDemarkSequentialPhase(IntEnum):
    """Represents the different phases of the TomDemark Sequential indicator."""

    NONE = 0
    BUY_SETUP = 1
    SELL_SETUP = 2
    BUY_COUNTDOWN = 3
    SELL_COUNTDOWN = 4
    BUY_SETUP_PERFECT = 5
    SELL_SETUP_PERFECT = 6


def calculate_tomdemark_sequential(
    df: pd.DataFrame,
    open_col: str = "open",
    high_col: str = "high",
    low_col: str = "low",
    close_col: str = "close",
) -> pd.DataFrame:
    """
    Calculate TomDeMark Sequential indicator.

    The TD Sequential identifies potential trend exhaustion points through two phases:

    1. **Setup Phase**: Detects a trend by counting 9 consecutive bars where the close is
       less than (Buy Setup) or greater than (Sell Setup) the close 4 bars earlier.

    2. **Countdown Phase**: After a valid setup completes, counts 13 qualifying bars
       (not necessarily consecutive) where the close is less than (Buy Countdown) or
       greater than (Sell Countdown) the low/high 2 bars earlier.

    The indicator also tracks TDST Support/Resistance levels which are used to validate
    the countdown phase continuation.

    Args:
        df: DataFrame with OHLC price data. Must have a date/timestamp column and OHLC prices.
        open_col: Column name for opening prices (default "open")
        high_col: Column name for high prices (default "high")
        low_col: Column name for low prices (default "low")
        close_col: Column name for closing prices (default "close")

    Returns:
        DataFrame with added TD Sequential columns:
        - TD_Phase: Current phase (0=None, 1=BuySetup, 2=SellSetup, 3=BuyCountdown,
                    4=SellCountdown, 5=BuySetupPerfect, 6=SellSetupPerfect)
        - TD_Setup_Count: Setup counter (1-9 during setup phase, 0 otherwise)
        - TD_Countdown_Count: Countdown counter (1-13 during countdown phase, 0 otherwise)
        - TD_Support_Price: Support level calculated from buy setup (TDST Support)
        - TD_Resistance_Price: Resistance level calculated from sell setup (TDST Resistance)
        - TD_Phase_Name: Human-readable phase name

    Example:
        >>> from poornull.data import download_daily
        >>> df = download_daily("600036", "20240101", "20241231")
        >>> df = calculate_tomdemark_sequential(df)
        >>> print(df[["date", "close", "TD_Phase_Name", "TD_Setup_Count", "TD_Countdown_Count"]].tail())
    """
    # Constants from Lean implementation
    max_setup_count = 9
    max_countdown_count = 13
    required_samples = 6

    df = df.copy()

    # Sort by date to ensure proper calculation order
    date_col = None
    for col in df.columns:
        col_lower = str(col).lower()
        if "date" in col_lower or "timestamp" in col_lower or "日期" in str(col):
            date_col = col
            break

    if date_col:
        df = df.sort_values(by=date_col).reset_index(drop=True)
    else:
        # If no date column found, sort by first column as fallback
        df = df.sort_values(by=df.columns[0]).reset_index(drop=True)

    # Validate required columns exist
    required_cols = [open_col, high_col, low_col, close_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Required columns {missing_cols} not found in DataFrame. Available columns: {list(df.columns)}"
        )

    # Initialize result columns
    df["TD_Phase"] = TomDemarkSequentialPhase.NONE
    df["TD_Setup_Count"] = 0
    df["TD_Countdown_Count"] = 0
    df["TD_Support_Price"] = np.nan
    df["TD_Resistance_Price"] = np.nan

    # State variables
    current_phase = TomDemarkSequentialPhase.NONE
    setup_count = 0
    countdown_count = 0
    support_price = np.nan
    resistance_price = np.nan

    # Process each bar
    for i in range(len(df)):
        if i < required_samples:
            # Not enough data yet
            df.at[i, "TD_Phase"] = TomDemarkSequentialPhase.NONE
            continue

        # Get current and historical bars
        current = df.iloc[i]
        bar_4_ago = df.iloc[i - 4] if i >= 4 else None
        bar_2_ago = df.iloc[i - 2] if i >= 2 else None

        # Initialize setup if nothing is active
        if current_phase == TomDemarkSequentialPhase.NONE:
            if i >= 5:
                prev_bar = df.iloc[i - 1]
                prev_bar_4_ago = df.iloc[i - 5]

                # Bearish flip: prev close > prev close[4] and current close < close[4]
                if prev_bar[close_col] > prev_bar_4_ago[close_col] and current[close_col] < bar_4_ago[close_col]:
                    current_phase = TomDemarkSequentialPhase.BUY_SETUP
                    setup_count = 1
                    df.at[i, "TD_Phase"] = TomDemarkSequentialPhase.BUY_SETUP
                    df.at[i, "TD_Setup_Count"] = setup_count

                # Bullish flip: prev close < prev close[4] and current close > close[4]
                elif prev_bar[close_col] < prev_bar_4_ago[close_col] and current[close_col] > bar_4_ago[close_col]:
                    current_phase = TomDemarkSequentialPhase.SELL_SETUP
                    setup_count = 1
                    df.at[i, "TD_Phase"] = TomDemarkSequentialPhase.SELL_SETUP
                    df.at[i, "TD_Setup_Count"] = setup_count

        # Handle Buy Setup
        elif current_phase == TomDemarkSequentialPhase.BUY_SETUP:
            if current[close_col] < bar_4_ago[close_col]:
                setup_count += 1

                if setup_count == max_setup_count:
                    # Setup complete - check if perfect
                    setup_bars = df.iloc[i - max_setup_count + 1 : i + 1]
                    is_perfect = _is_buy_setup_perfect(setup_bars, low_col)

                    # Calculate resistance (highest high of 9-bar setup)
                    resistance_price = setup_bars[high_col].max()

                    # Transition to countdown
                    current_phase = TomDemarkSequentialPhase.BUY_COUNTDOWN
                    countdown_count = 0

                    # Check if bar 9 qualifies for countdown
                    if current[close_col] < bar_2_ago[low_col]:
                        countdown_count = 1

                    phase = (
                        TomDemarkSequentialPhase.BUY_SETUP_PERFECT if is_perfect else TomDemarkSequentialPhase.BUY_SETUP
                    )
                    df.at[i, "TD_Phase"] = phase
                    df.at[i, "TD_Setup_Count"] = setup_count
                    df.at[i, "TD_Countdown_Count"] = countdown_count
                    df.at[i, "TD_Resistance_Price"] = resistance_price
                    setup_count = 0
                else:
                    df.at[i, "TD_Phase"] = TomDemarkSequentialPhase.BUY_SETUP
                    df.at[i, "TD_Setup_Count"] = setup_count
            else:
                # Setup broken
                current_phase = TomDemarkSequentialPhase.NONE
                setup_count = 0
                df.at[i, "TD_Phase"] = TomDemarkSequentialPhase.NONE

        # Handle Sell Setup
        elif current_phase == TomDemarkSequentialPhase.SELL_SETUP:
            if current[close_col] > bar_4_ago[close_col]:
                setup_count += 1

                if setup_count == max_setup_count:
                    # Setup complete - check if perfect
                    setup_bars = df.iloc[i - max_setup_count + 1 : i + 1]
                    is_perfect = _is_sell_setup_perfect(setup_bars, high_col)

                    # Calculate support (lowest low of 9-bar setup)
                    support_price = setup_bars[low_col].min()

                    # Transition to countdown
                    current_phase = TomDemarkSequentialPhase.SELL_COUNTDOWN
                    countdown_count = 0

                    # Check if bar 9 qualifies for countdown
                    if current[close_col] > bar_2_ago[high_col]:
                        countdown_count = 1

                    phase = (
                        TomDemarkSequentialPhase.SELL_SETUP_PERFECT
                        if is_perfect
                        else TomDemarkSequentialPhase.SELL_SETUP
                    )
                    df.at[i, "TD_Phase"] = phase
                    df.at[i, "TD_Setup_Count"] = setup_count
                    df.at[i, "TD_Countdown_Count"] = countdown_count
                    df.at[i, "TD_Support_Price"] = support_price
                    setup_count = 0
                else:
                    df.at[i, "TD_Phase"] = TomDemarkSequentialPhase.SELL_SETUP
                    df.at[i, "TD_Setup_Count"] = setup_count
            else:
                # Setup broken
                current_phase = TomDemarkSequentialPhase.NONE
                setup_count = 0
                df.at[i, "TD_Phase"] = TomDemarkSequentialPhase.NONE

        # Handle Buy Countdown
        elif current_phase == TomDemarkSequentialPhase.BUY_COUNTDOWN:
            # Check if close breaks resistance (invalidates countdown)
            if current[close_col] > resistance_price:
                current_phase = TomDemarkSequentialPhase.NONE
                countdown_count = 0
                resistance_price = np.nan
                df.at[i, "TD_Phase"] = TomDemarkSequentialPhase.NONE
            elif current[close_col] <= bar_2_ago[low_col]:
                # Qualifying countdown bar
                countdown_count += 1
                df.at[i, "TD_Phase"] = TomDemarkSequentialPhase.BUY_COUNTDOWN
                df.at[i, "TD_Countdown_Count"] = countdown_count
                df.at[i, "TD_Resistance_Price"] = resistance_price

                if countdown_count == max_countdown_count:
                    # Countdown complete - reset
                    current_phase = TomDemarkSequentialPhase.NONE
                    countdown_count = 0
                    resistance_price = np.nan
            else:
                # Non-qualifying bar, keep countdown active
                df.at[i, "TD_Phase"] = TomDemarkSequentialPhase.NONE
                df.at[i, "TD_Resistance_Price"] = resistance_price

        # Handle Sell Countdown
        elif current_phase == TomDemarkSequentialPhase.SELL_COUNTDOWN:
            # Check if close breaks support (invalidates countdown)
            if current[close_col] < support_price:
                current_phase = TomDemarkSequentialPhase.NONE
                countdown_count = 0
                support_price = np.nan
                df.at[i, "TD_Phase"] = TomDemarkSequentialPhase.NONE
            elif current[close_col] >= bar_2_ago[high_col]:
                # Qualifying countdown bar
                countdown_count += 1
                df.at[i, "TD_Phase"] = TomDemarkSequentialPhase.SELL_COUNTDOWN
                df.at[i, "TD_Countdown_Count"] = countdown_count
                df.at[i, "TD_Support_Price"] = support_price

                if countdown_count == max_countdown_count:
                    # Countdown complete - reset
                    current_phase = TomDemarkSequentialPhase.NONE
                    countdown_count = 0
                    support_price = np.nan
            else:
                # Non-qualifying bar, keep countdown active
                df.at[i, "TD_Phase"] = TomDemarkSequentialPhase.NONE
                df.at[i, "TD_Support_Price"] = support_price

    # Add human-readable phase names
    phase_names = {
        TomDemarkSequentialPhase.NONE: "None",
        TomDemarkSequentialPhase.BUY_SETUP: "Buy Setup",
        TomDemarkSequentialPhase.SELL_SETUP: "Sell Setup",
        TomDemarkSequentialPhase.BUY_COUNTDOWN: "Buy Countdown",
        TomDemarkSequentialPhase.SELL_COUNTDOWN: "Sell Countdown",
        TomDemarkSequentialPhase.BUY_SETUP_PERFECT: "Buy Setup Perfect",
        TomDemarkSequentialPhase.SELL_SETUP_PERFECT: "Sell Setup Perfect",
    }
    df["TD_Phase_Name"] = df["TD_Phase"].map(phase_names)

    return df


def _is_buy_setup_perfect(setup_bars: pd.DataFrame, low_col: str) -> bool:
    """
    Check if a buy setup is "perfect".

    A buy setup is perfect if bar 8 or bar 9 has a low less than both bar 6 and bar 7.

    Args:
        setup_bars: DataFrame containing the 9 setup bars (indexed 0-8)
        low_col: Name of the low price column

    Returns:
        True if the setup is perfect, False otherwise
    """
    if len(setup_bars) < 9:
        return False

    bar_6 = setup_bars.iloc[5]
    bar_7 = setup_bars.iloc[6]
    bar_8 = setup_bars.iloc[7]
    bar_9 = setup_bars.iloc[8]

    return (bar_8[low_col] < bar_6[low_col] and bar_8[low_col] < bar_7[low_col]) or (
        bar_9[low_col] < bar_6[low_col] and bar_9[low_col] < bar_7[low_col]
    )


def _is_sell_setup_perfect(setup_bars: pd.DataFrame, high_col: str) -> bool:
    """
    Check if a sell setup is "perfect".

    A sell setup is perfect if bar 8 or bar 9 has a high greater than both bar 6 and bar 7.

    Args:
        setup_bars: DataFrame containing the 9 setup bars (indexed 0-8)
        high_col: Name of the high price column

    Returns:
        True if the setup is perfect, False otherwise
    """
    if len(setup_bars) < 9:
        return False

    bar_6 = setup_bars.iloc[5]
    bar_7 = setup_bars.iloc[6]
    bar_8 = setup_bars.iloc[7]
    bar_9 = setup_bars.iloc[8]

    return (bar_8[high_col] > bar_6[high_col] and bar_8[high_col] > bar_7[high_col]) or (
        bar_9[high_col] > bar_6[high_col] and bar_9[high_col] > bar_7[high_col]
    )


# ===== PriceHistory API =====


def with_tomdemark(history: PriceHistory) -> PriceHistory:
    """
    Add TomDeMark Sequential indicators to PriceHistory.

    Args:
        history: PriceHistory object with OHLC data

    Returns:
        New PriceHistory with TD Sequential columns added:
        - TD_Phase: Current phase (0-6)
        - TD_Setup_Count: Setup counter (1-9 during setup, 0 otherwise)
        - TD_Countdown_Count: Countdown counter (1-13 during countdown, 0 otherwise)
        - TD_Support_Price: Support level from buy setup
        - TD_Resistance_Price: Resistance level from sell setup
        - TD_Phase_Name: Human-readable phase name

    Example:
        >>> from poornull.data import PriceHistory
        >>> from poornull.data import download_daily
        >>> df = download_daily("600036", "20240101", "20241231")
        >>> history = PriceHistory(df)
        >>> history = with_tomdemark(history)
        >>> print(f"Has TD_Phase: {history.has_indicator('TD_Phase')}")
    """
    df = calculate_tomdemark_sequential(history.df)
    return PriceHistory(df)
