# Trading Strategy Backtesting System

A comprehensive backtesting system for trading strategies with focus on short-bias trading and Steven Dux-style strategies. The system fetches data from Polygon.io and exports results to Excel for easy analysis and parameter modification.

## Features

- **Multiple Trading Strategies**:

  - Gap Up Short (70%+ gap, target 50% retrace)
  - First Red Day (after extended green streak)
  - Extended Gap Down (5%+ gap down)
  - Gap Fill Close (long strategy for 100%+ gaps)
  - Multi-day Breakout (volume + price breakout)

- **Steven Dux Dollar Block Metric**: Proprietary calculation (Average Consolidation Price × Volume)
- **Float Rotation Analysis**: Volume/Float ratio for liquidity analysis
- **Excel Integration**: User-friendly Excel output with all your requested columns
- **Parameter Optimization**: Easy configuration without coding knowledge
- **Risk Management**: Configurable position sizing and stop losses

## Quick Start

### 1. Setup

```bash
# Install required packages (already done)
pip install pandas requests openpyxl polygon-api-client numpy yfinance

# Get a Polygon.io API key (optional, system will use Yahoo Finance as fallback)
# Sign up at https://polygon.io
```

### 2. Configure API Key

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Then edit `.env` and add your API key:

```
POLYGON_API_KEY=your_actual_api_key_here
```

**Important: Never commit the `.env` file to version control!**

### 3. Run the System

```bash
python main.py
```

### 4. Easy Excel Configuration

The system creates `strategy_parameters_template.xlsx` where you can modify all strategy parameters without coding.

**Important**: Parameters are read from Excel if the template exists, otherwise from config.py. See [PARAMETER_LOADING.md](PARAMETER_LOADING.md) for detailed explanation.

## Parameter Configuration

### Where Does the System Read Parameters From?

For actual backtesting, the system reads parameters in this order:

1. **Excel file** (`strategy_parameters_template.xlsx`) - **IF IT EXISTS** ✨ Recommended
2. **config.py** - **IF Excel file doesn't exist**

**See [PARAMETER_LOADING.md](PARAMETER_LOADING.md) for complete details on parameter loading.**

### Quick Guide: Modifying Parameters

#### Option A: Excel (Non-Programmers) ✨

1. Run `python main.py` and choose option 5 (Create Parameter Template)
2. Open `strategy_parameters_template.xlsx`
3. Modify values in the "Current Value" column
4. Save the file
5. Restart the program - your changes are automatically used!

#### Option B: config.py (Programmers)

1. Delete the Excel template: `rm strategy_parameters_template.xlsx`
2. Edit `config.py` directly
3. Restart the program

## Excel Output Columns

The system exports results with exactly the columns you requested:

- `Date`, `Ticker`, `Setup Type`, `Entry`, `Exit`, `Shares`
- `P&L ($)`, `P&L (%)`, `Win/Loss`, `Risk ($)`
- `Float (M)`, `Vol (M)`, `Rotation`, `Setup Quality`
- `Mistake Tag`, `Pattern Notes`
- **Additional:** `Gap %`, `Dollar Block`, `Target Hit`, `Stop Hit`

## Strategy Parameters (Easy to Modify)

### Gap Up Short Strategy

```python
'min_gap_percent': 70,        # Minimum gap up %
'target_retrace_percent': 50, # Target retrace %
'max_float_millions': 50,     # Max float size
'min_volume_millions': 1,     # Min volume required
```

### First Red Day Strategy

```python
'min_green_days': 20,         # Min consecutive green days
'max_float_millions': 100,    # Max float size
'min_volume_millions': 2,     # Min volume required
```

### Extended Gap Down Strategy

```python
'min_gap_down_percent': 5,    # Min gap down %
'max_float_millions': 200,    # Max float size
'min_volume_millions': 1,     # Min volume required
```

## Usage Examples

### 1. Quick Test (Recommended First Run)

```python
python main.py
# Choose option 6: Quick Test (Last 30 Days)
```

### 2. Full Backtest

```python
python main.py
# Choose option 1: Run Full Backtest
# Enter tickers: AMC,GME,SPRT,IRNT,DWAC
```

### 3. Single Stock Analysis

```python
python main.py
# Choose option 2: Test Single Stock
# Enter ticker: AMC
```

### 4. Modify Parameters

```python
python main.py
# Choose option 5: Create Parameter Template
# Edit the generated Excel file
# Run backtest again with new parameters
```

## Files Structure

- `main.py` - User-friendly interface
- `config.py` - All configurable parameters
- `backtest_engine.py` - Main backtesting logic
- `data_fetcher.py` - Polygon.io and Yahoo Finance data
- `strategies.py` - All trading strategies
- `excel_export.py` - Excel reporting and formatting

## Strategy Details

### Gap Up Short

- Targets stocks that gap up 70%+
- Expects 50% retrace of the gap
- Risk management: Stop at previous day high
- Best for: Low float, high volume momentum stocks

### First Red Day

- Finds stocks after 20+ consecutive green days
- Enters on first red day
- Targets: Extended overvalued momentum breaks
- Risk: High of consolidation or previous day

### Extended Gap Down

- Targets stocks gapping down 5%+
- Continuation short strategy
- Risk: Previous open or high
- Best for: Momentum breakdown plays

### Dollar Block Calculation

Steven Dux's proprietary metric:

```
Dollar Block = Average Consolidation Price × Volume in Range
```

- Measures dollar flow in consolidation
- Higher values = more institutional interest
- Used for entry timing and risk assessment

## Customization for Non-Programmers

### Method 1: Excel Parameter Template

1. Run `python main.py`
2. Choose option 5 (Create Parameter Template)
3. Open `strategy_parameters_template.xlsx`
4. Modify the "Current Value" column
5. Save and run backtest again

### Method 2: Edit config.py

Open `config.py` in any text editor and modify values:

```python
# Make gap up strategy more selective
'min_gap_percent': 100,  # Changed from 70 to 100

# Target smaller retracements
'target_retrace_percent': 30,  # Changed from 50 to 30

# Focus on smaller float stocks
'max_float_millions': 20,  # Changed from 50 to 20
```

## Risk Management

The system includes comprehensive risk management:

- **Position Sizing**: Fixed dollar amount or percentage of portfolio
- **Stop Losses**: Configurable percentage-based stops
- **Commission**: Realistic per-share commission costs
- **Slippage**: Market impact modeling

## Output Analysis

### Excel Sheets Generated:

1. **Trades**: All individual trades with your requested columns
2. **Summary**: Win rates, profit factors, strategy breakdown
3. **Configuration**: Current parameter settings

### Key Metrics:

- Win Rate %
- Total P&L
- Average Win/Loss
- Profit Factor
- Maximum Drawdown
- Strategy-specific breakdowns

## Optimization

The system can optimize parameters automatically:

```python
# Run parameter optimization
python main.py
# Choose option 3: Optimize Strategy Parameters
```

This tests different parameter combinations and finds the best performing settings.

## Data Sources

- **Primary**: Polygon.io (paid, high-quality data)
- **Fallback**: Yahoo Finance (free, limited features)
- **Float Data**: Estimated from Yahoo Finance info

## Best Practices

1. **Start Small**: Use Quick Test first
2. **Paper Trade**: Test strategies before live trading
3. **Regular Updates**: Market conditions change, re-optimize periodically
4. **Risk Control**: Never risk more than you can afford to lose
5. **Multiple Timeframes**: Test different date ranges

## Troubleshooting

### No Signals Generated

- Try different tickers (AMC, GME, SPRT work well)
- Extend date range (try 6 months)
- Lower strategy parameters (reduce gap requirements)

### API Errors

- Check Polygon.io API key in config.py
- System will fallback to Yahoo Finance automatically
- Free tier has rate limits

### Excel Issues

- Ensure openpyxl is installed
- Close Excel files before running backtest
- Check file permissions

## Advanced Usage

### Custom Tickers List

Create a text file with your watchlist:

```python
# In main.py, modify get_ticker_list() function
# Or edit the default tickers list
```

### Strategy Modifications

Each strategy is in `strategies.py` with clear logic. You can:

- Modify entry/exit conditions
- Add new filters
- Combine multiple strategies
- Create custom metrics

## Support

This system is designed to be self-contained and user-friendly. Key files to modify:

1. **config.py** - All parameters
2. **main.py** - User interface
3. **Excel templates** - Parameter modification

For advanced customization, the code is well-commented and modular.

## Performance Notes

- **Data Fetching**: ~1-2 seconds per ticker
- **Strategy Processing**: Nearly instantaneous
- **Excel Export**: ~5-10 seconds for large datasets
- **Memory Usage**: Minimal, handles 100+ tickers easily

Start with the Quick Test option to verify everything works, then customize parameters based on your trading style!
