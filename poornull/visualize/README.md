# Visualization Module

Modular visualization components for stock charts and technical indicators.

## Quick Start

```python
from poornull.data import download_daily
from poornull.indicators import calculate_ma_ema
from poornull.visualize import create_stock_chart

# Download and prepare data
df = download_daily("600036", "20240101", "20241231")
df = calculate_ma_ema(df)

# Create chart
create_stock_chart(df, show_ma=True, save_path="chart.png")
```

## Module Structure

- **base.py** - Base utilities (style, figure creation, date handling)
- **candlestick.py** - Candlestick and price line plotting
- **ma.py** - Moving average plotting and crossovers
- **trendline.py** - Trendline and support/resistance plotting
- **tomdemark.py** - TomDeMark Sequential indicator plotting
- **chart.py** - High-level chart composition functions

## Features

- ✅ Modular design - mix and match components
- ✅ Auto-detection of date columns
- ✅ Support for candlesticks and line charts
- ✅ Moving averages (MA/EMA)
- ✅ Trendlines (linear, support/resistance)
- ✅ TomDeMark Sequential visualization
- ✅ Custom compositions

## Examples

See `scripts/example_visualization.py` for complete examples.

## Documentation

See `docs/VISUALIZATION.md` for detailed documentation.
