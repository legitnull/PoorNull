# Scripts

Utility scripts for stock analysis and data processing.

## compute_ma_ema.py

Compute or fetch MA/EMA (Moving Average/Exponential Moving Average) values for stocks.

### Features

- Compute MA/EMA values locally using pandas
- Option to fetch from akshare if available
- Process single stocks or entire watchlists
- Customizable MA/EMA periods
- Flexible date ranges

### Usage

#### Process a single stock:

```bash
python scripts/compute_ma_ema.py --stock 600036
```

#### Process a watchlist:

```bash
python scripts/compute_ma_ema.py --watchlist default
```

#### Custom MA/EMA periods:

```bash
python scripts/compute_ma_ema.py --stock 600036 --ma-periods 5,10,20,30,60 --ema-periods 5,10,20,30,60
```

#### Custom date range:

```bash
python scripts/compute_ma_ema.py --stock 600036 --start-date 20240101 --end-date 20241231
```

#### Process specific watchlist:

```bash
python scripts/compute_ma_ema.py --watchlist banking
```

### Options

- `--stock`: Process a single stock code
- `--watchlist`: Watchlist name (default: "default")
- `--start-date`: Start date in YYYYMMDD format (default: 200 days ago)
- `--end-date`: End date in YYYYMMDD format (default: today)
- `--ma-periods`: Comma-separated MA periods (default: 5,10,20,30,60)
- `--ema-periods`: Comma-separated EMA periods (default: 5,10,20,30,60)

### Examples

```bash
# Compute MA/EMA for 招商银行
python scripts/compute_ma_ema.py --stock 600036

# Process all stocks in banking watchlist
python scripts/compute_ma_ema.py --watchlist banking

# Custom periods for energy stocks
python scripts/compute_ma_ema.py --watchlist energy --ma-periods 10,20,30 --ema-periods 10,20,30
```

## fetch_stock_categories.py

Fetch stock industry/category information from akshare and organize watchlists by category.

### Usage

```bash
python scripts/fetch_stock_categories.py
```

This script will:
1. Fetch industry information for all stocks in the default watchlist
2. Categorize stocks by industry
3. Generate categorized watchlist code that can be copied to `watchlists.py`
