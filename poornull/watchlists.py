"""
Watchlists for manually selected stocks.

This module contains predefined watchlists of stock codes for easy access.
You can organize stocks by category, strategy, or any other grouping.
"""

# Example watchlists - customize these with your stock codes
WATCHLISTS = {
    "default": [
        "600690",  # 海尔智家
        "603516",  # 淳中科技
        "601088",  # 中国神华
        "510720",  # 红利国企 ETF
        "601985",  # 中国核电
        "003816",  # 中国广核
        "601066",  # 中信建投
        "601398",  # 工商银行
        "002142",  # 宁波银行
        "600030",  # 中信证券
        "601998",  # 中信银行
        "600685",  # 中船防务
        "600733",  # 北汽蓝谷
        "000538",  # 云南白药
        "600519",  # 贵州茅台
        "000858",  # 五粮液
        "600600",  # 青岛啤酒
        "000333",  # 美的集团
        "600900",  # 长江电力
        "600886",  # 国投电力
        "601728",  # 中国电信
        "000651",  # 格力电器
        "600887",  # 伊利股份
        "600941",  # 中国移动
        "600028",  # 中国石化
        "601919",  # 中远海控
        "601336",  # 新华保险
        "601318",  # 中国平安
        "600036",  # 招商银行
    ],
    # Banking & Finance
    "banking": [
        "601398",  # 工商银行
        "002142",  # 宁波银行
        "601998",  # 中信银行
        "600036",  # 招商银行
    ],
    # Securities & Investment
    "securities": [
        "601066",  # 中信建投
        "600030",  # 中信证券
    ],
    # Insurance
    "insurance": [
        "601336",  # 新华保险
        "601318",  # 中国平安
    ],
    # Energy & Power
    "energy": [
        "601088",  # 中国神华
        "601985",  # 中国核电
        "003816",  # 中国广核
        "600900",  # 长江电力
        "600886",  # 国投电力
        "600028",  # 中国石化
    ],
    # Technology & Communication
    "technology": [
        "603516",  # 淳中科技
        "601728",  # 中国电信
        "600941",  # 中国移动
    ],
    # Consumer Goods - Food & Beverage
    "food_beverage": [
        "000538",  # 云南白药
        "600519",  # 贵州茅台
        "000858",  # 五粮液
        "600600",  # 青岛啤酒
        "600887",  # 伊利股份
    ],
    # Consumer Goods - Home Appliances
    "home_appliances": [
        "600690",  # 海尔智家
        "000333",  # 美的集团
        "000651",  # 格力电器
    ],
    # Transportation & Logistics
    "transportation": [
        "600685",  # 中船防务
        "600733",  # 北汽蓝谷
        "601919",  # 中远海控
    ],
    # ETFs
    "etf": [
        "510720",  # 红利国企 ETF
    ],
}

# Flattened list of all unique stocks across all watchlists
ALL_STOCKS = sorted({stock for stocks in WATCHLISTS.values() for stock in stocks})


def get_watchlist(name: str = "default") -> list[str]:
    """
    Get a watchlist by name.

    Args:
        name: Name of the watchlist (default: "default")

    Returns:
        List of stock codes in the watchlist

    Raises:
        KeyError: If watchlist name doesn't exist

    Example:
        >>> stocks = get_watchlist("default")
        >>> print(stocks)
        ['600036']
    """
    if name not in WATCHLISTS:
        available = ", ".join(WATCHLISTS.keys())
        raise KeyError(f"Watchlist '{name}' not found. Available watchlists: {available}")
    return WATCHLISTS[name].copy()


def get_all_stocks() -> list[str]:
    """
    Get all unique stocks from all watchlists.

    Returns:
        Sorted list of all unique stock codes

    Example:
        >>> all_stocks = get_all_stocks()
        >>> print(all_stocks)
        ['600036']
    """
    return ALL_STOCKS.copy()


def list_watchlists() -> list[str]:
    """
    List all available watchlist names.

    Returns:
        List of watchlist names

    Example:
        >>> watchlists = list_watchlists()
        >>> print(watchlists)
        ['default']
    """
    return list(WATCHLISTS.keys())


def add_stock_to_watchlist(stock_code: str, watchlist_name: str = "default") -> None:
    """
    Add a stock to a watchlist.

    Args:
        stock_code: Stock code to add (e.g., "600036")
        watchlist_name: Name of the watchlist (default: "default")

    Example:
        >>> add_stock_to_watchlist("000001", "default")
    """
    if watchlist_name not in WATCHLISTS:
        WATCHLISTS[watchlist_name] = []
    if stock_code not in WATCHLISTS[watchlist_name]:
        WATCHLISTS[watchlist_name].append(stock_code)
        # Update ALL_STOCKS
        global ALL_STOCKS
        ALL_STOCKS = sorted({stock for stocks in WATCHLISTS.values() for stock in stocks})


def remove_stock_from_watchlist(stock_code: str, watchlist_name: str = "default") -> None:
    """
    Remove a stock from a watchlist.

    Args:
        stock_code: Stock code to remove (e.g., "600036")
        watchlist_name: Name of the watchlist (default: "default")

    Example:
        >>> remove_stock_from_watchlist("600036", "default")
    """
    if watchlist_name in WATCHLISTS and stock_code in WATCHLISTS[watchlist_name]:
        WATCHLISTS[watchlist_name].remove(stock_code)
        # Update ALL_STOCKS
        global ALL_STOCKS
        ALL_STOCKS = sorted({stock for stocks in WATCHLISTS.values() for stock in stocks})
