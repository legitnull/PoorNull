"""
Script to fetch stock categories/industries from akshare and organize watchlists.

This script fetches industry information for stocks and categorizes them.
"""

import sys
from pathlib import Path

# Add parent directory to path to import poornull
sys.path.insert(0, str(Path(__file__).parent.parent))

import akshare as ak

from poornull.watchlists import get_watchlist


def get_stocks_industry_batch(stock_codes: list[str]) -> dict[str, dict]:
    """
    Get stock industry information in batch for better performance.

    Args:
        stock_codes: List of stock codes

    Returns:
        Dictionary mapping stock codes to their info
    """
    print("📊 Fetching stock information in batch...")
    stock_info = {}

    try:
        # Get all A-share spot data which includes industry info
        print("Fetching all A-share stock data...")
        spot_data = ak.stock_zh_a_spot_em()

        # Create mapping
        for code in stock_codes:
            # Try to find the stock in spot data
            matches = spot_data[spot_data["代码"] == code]
            if not matches.empty:
                row = matches.iloc[0]
                stock_info[code] = {
                    "code": code,
                    "name": row.get("名称", ""),
                    "industry": row.get("所属行业", "未知"),
                }
            else:
                stock_info[code] = {
                    "code": code,
                    "name": "",
                    "industry": "未知",
                }

        print(f"✅ Found information for {len([s for s in stock_info.values() if s['industry'] != '未知'])} stocks")
    except Exception as e:
        print(f"⚠️  Error fetching batch data: {e}")
        # Fallback: set all to unknown
        for code in stock_codes:
            stock_info[code] = {"code": code, "name": "", "industry": "未知"}

    return stock_info


def categorize_stocks(stock_codes: list[str]) -> tuple[dict[str, list[str]], dict[str, dict]]:
    """
    Categorize stocks by industry.

    Args:
        stock_codes: List of stock codes

    Returns:
        Tuple of (categories dict, stock_info dict)
    """
    categories = {}

    # Get stock info in batch
    stock_info = get_stocks_industry_batch(stock_codes)

    print("\n" + "=" * 80)
    print("📋 Stock Information:")
    print("=" * 80)

    for code in stock_codes:
        info = stock_info[code]
        industry = info.get("industry", "未知")
        name = info.get("name", "")

        if industry not in categories:
            categories[industry] = []

        categories[industry].append(code)
        print(f"{code}  # {name} - {industry}")

    print("\n" + "=" * 80)
    print("📋 Categorization Summary:")
    print("=" * 80)
    for industry, codes in sorted(categories.items()):
        print(f"\n{industry} ({len(codes)} stocks):")
        for code in codes:
            info = stock_info[code]
            name = info.get("name", "")
            print(f"  - {code}  # {name}")

    return categories, stock_info


def main():
    """Main function to fetch and categorize stocks."""
    # Get stocks from default watchlist
    stocks = get_watchlist("default")
    print(f"Found {len(stocks)} stocks in default watchlist\n")

    # Categorize stocks
    categories, stock_info = categorize_stocks(stocks)

    # Generate categorized watchlist code
    print("\n" + "=" * 80)
    print("📝 Categorized Watchlist Code:")
    print("=" * 80)
    print("\nWATCHLISTS = {")
    print('    "default": [')
    for code in stocks:
        info = stock_info[code]
        name = info.get("name", "")
        print(f'        "{code}",  # {name}')
    print("    ],")

    # Print categorized watchlists
    for industry, codes in sorted(categories.items()):
        if industry == "未知" or not industry:
            continue
        # Clean industry name for use as key
        key = industry.replace(" ", "_").replace("/", "_").replace("-", "_")
        print(f'\n    "{key}": [  # {industry}')
        for code in codes:
            info = stock_info[code]
            name = info.get("name", "")
            print(f'        "{code}",  # {name}')
        print("    ],")

    print("}")


if __name__ == "__main__":
    main()
