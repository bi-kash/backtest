# Trading Strategy Implementation Details

This document provides detailed implementation specifics for each trading strategy in the backtesting system.

## Table of Contents

1. [Gap Up Short Strategy](#1-gap-up-short-strategy)
2. [First Red Day Strategy](#2-first-red-day-strategy)
3. [Extended Gap Down Strategy](#3-extended-gap-down-strategy)
4. [Gap Fill Close Strategy](#4-gap-fill-close-strategy)
5. [Multi-day Breakout Strategy](#5-multi-day-breakout-strategy)
6. [Technical Implementation Notes](#6-technical-implementation-notes)

---

## 1. Gap Up Short Strategy

### Strategy Overview

This strategy targets stocks that gap up significantly on high volume, betting on a retrace back toward the previous day's closing price.

### Entry Criteria

```python
# Configuration (config.py)
'gap_up_short': {
    'enabled': True,
    'min_gap_percent': 70,          # Minimum gap up percentage
    'target_retrace_percent': 50,   # Target retrace for profit
    'max_float_millions': 50,       # Maximum float in millions
    'min_volume_millions': 1,       # Minimum volume in millions
}
```

### Implementation Logic

1. **Gap Calculation**: `((current_open - previous_close) / previous_close) * 100`
2. **Entry Conditions**:
   - Gap ≥ 70% (configurable)
   - Float ≤ 50M shares (smaller companies more volatile)
   - Volume ≥ 1M shares (sufficient liquidity)
3. **Entry Price**: Market open after the gap
4. **Target Price**: `current_open - (gap_amount * 50%)`
5. **Stop Loss**: `max(previous_day_high, current_day_high)`

### Exit Logic

- **Target Hit**: Exit at 50% retrace of gap
- **Stop Hit**: Exit at stop loss level
- **Same Day Close**: If neither hit, exit at day's close

### Risk Profile

- **High Risk/High Reward**: Large gaps can continue higher
- **Quick Moves**: Usually resolves same day
- **Float Sensitive**: Smaller floats more likely to retrace

---

## 2. First Red Day Strategy

### Strategy Overview

After an extended run of consecutive green days (20+), this strategy shorts the first red day, anticipating a larger correction.

### Entry Criteria

```python
# Configuration (config.py)
'first_red_day': {
    'enabled': True,
    'min_green_days': 20,      # Minimum consecutive green days before
    'max_float_millions': 100,  # Maximum float
    'min_volume_millions': 2,   # Minimum volume
}
```

### Implementation Logic

1. **Green Day Detection**: `close > open` for each day
2. **Consecutive Count**: Walk backward from current red day
3. **Entry Conditions**:
   - Current day is red (`close < open`)
   - Previous 20+ days were all green
   - Float ≤ 100M shares
   - Volume ≥ 2M shares
4. **Entry Price**: Close of the first red day
5. **Target Price**: `entry_price * 0.8` (20% down)
6. **Stop Loss**: `max(current_day_high, previous_day_high)`

### Exit Logic (Look-forward up to 10 days)

- **Target Hit**: 20% decline from entry
- **Stop Hit**: Price goes above stop loss
- **Timeout**: Use close price of final day examined

### Psychological Basis

- **Exhaustion**: Long runs often end in reversals
- **Profit Taking**: Early holders start selling
- **Momentum Break**: First red day signals trend change

---

## 3. Extended Gap Down Strategy

### Strategy Overview

Shorts stocks that gap down significantly, betting they will continue falling rather than bounce back.

### Entry Criteria

```python
# Configuration (config.py)
'extended_gap_down': {
    'enabled': True,
    'min_gap_down_percent': 5,   # Minimum gap down percentage
    'max_float_millions': 200,   # Maximum float
    'min_volume_millions': 1,    # Minimum volume
}
```

### Implementation Logic

1. **Gap Calculation**: `((current_open - previous_close) / previous_close) * 100`
2. **Entry Conditions**:
   - Gap ≤ -5% (negative gap = gap down)
   - Float ≤ 200M shares
   - Volume ≥ 1M shares
3. **Entry Price**: Market open after gap down
4. **Target Price**: `entry_price * 0.9` (10% further down)
5. **Stop Loss**: `max(previous_day_open, previous_day_high)`

### Exit Logic (Look-forward up to 10 days)

- **Target Hit**: 10% decline from entry
- **Stop Hit**: Price bounces back to previous levels
- **Timeout**: Use close price of final day examined

### Market Context

- **Momentum Continuation**: Bad news often leads to more selling
- **Panic Selling**: Gap downs can trigger stop losses
- **Lower Risk**: Already gapped down, limited upside

---

## 4. Gap Fill Close Strategy (Long Strategy)

### Strategy Overview

The only long strategy in the system. Targets stocks that gap up massively but close near their opening price, indicating strength and potential continuation.

### Entry Criteria

```python
# Configuration (config.py)
'gap_fill_close': {
    'enabled': True,
    'min_gap_percent': 100,      # Minimum gap up percentage
    'entry_time': '15:59',       # Entry time (3:59 PM)
    'min_volume_millions': 1,    # Minimum volume
}
```

### Implementation Logic

1. **Gap Calculation**: `((current_open - previous_close) / previous_close) * 100`
2. **Close Strength**: `close_vs_open_ratio = current_close / current_open`
3. **Entry Conditions**:
   - Gap ≥ 100% (massive gap up)
   - Close within 5% of open (`close_vs_open_ratio ≥ 0.95`)
   - Volume ≥ 1M shares
4. **Entry Price**: Close price (simulating 3:59 PM entry)
5. **Exit Price**: Next day's close
6. **Target**: `entry_price * 1.1` (10% gain)
7. **Stop Loss**: `entry_price * 0.95` (5% loss)

### Strategy Logic

- **Strength Signal**: Holding gains after massive gap shows demand
- **Overnight Hold**: Benefits from continued momentum
- **Quick Exit**: Single day hold reduces risk

---

## 5. Multi-day Breakout Strategy

### Strategy Overview

Long strategy that identifies volume spikes coinciding with price breakouts above recent resistance levels.

### Entry Criteria

```python
# Configuration (config.py)
'multi_day_breakout': {
    'enabled': True,
    'min_volume_ratio': 2,       # Volume vs average volume ratio
    'min_volume_millions': 5,    # Minimum absolute volume
    'breakout_period_days': 5,   # Days to look back for high
}
```

### Implementation Logic

1. **Volume Analysis**:
   - Calculate 5-day average volume
   - Current volume must be 2x average
2. **Price Breakout**:
   - Current high > highest high of last 5 days
3. **Entry Conditions**:
   - Volume ratio ≥ 2.0
   - Price breakout confirmed
   - Volume ≥ 5M shares (institutional interest)
4. **Entry Price**: High of breakout day
5. **Target Price**: `entry_price * 1.15` (15% gain)
6. **Stop Loss**: Low of breakout day

### Exit Logic (Look-forward up to 10 days)

- **Target Hit**: 15% gain from entry
- **Stop Hit**: Price drops below breakout day low
- **Timeout**: Use close price of final day examined

### Technical Basis

- **Volume Confirmation**: High volume validates breakout
- **Resistance Break**: Above recent highs shows strength
- **Institutional Interest**: Large volume suggests smart money

---

## 6. Technical Implementation Notes

### Data Requirements

All strategies require:

```python
# Required columns in data DataFrame:
['date', 'open', 'high', 'low', 'close', 'volume', 'float_millions', 'volume_millions']
```

### Look-forward Mechanism

Most strategies use a look-forward approach to determine realistic exits:

```python
# Example from Extended Gap Down
max_lookforward = 10  # Look up to 10 days ahead

for j in range(i + 1, min(i + 1 + max_lookforward, len(data))):
    future_day = data.iloc[j]

    # Check exit conditions
    if future_day['high'] >= stop_loss:
        exit_price = stop_loss
        break
    elif future_day['low'] <= target_price:
        exit_price = target_price
        break
    else:
        exit_price = future_day['close']  # Keep updating until break
```

### Position Sizing

All strategies use the same position sizing logic:

```python
# From config.py
RISK_MANAGEMENT = {
    'max_risk_per_trade': 1000,      # Maximum $ risk per trade
    'stop_loss_percent': 10,         # Stop loss percentage
    'fixed_dollar_amount': 10000,    # Fixed dollar amount per trade
}

# Position size calculation
risk_per_share = abs(entry_price - stop_loss)
max_shares = max_risk_per_trade / risk_per_share
position_value = min(max_shares * entry_price, fixed_dollar_amount)
```

### Signal Output Structure

Each strategy returns signals in this format:

```python
signal = {
    'date': datetime,           # Trade date
    'ticker': str,              # Stock symbol
    'setup_type': str,          # Strategy name
    'entry': float,             # Entry price
    'exit': float,              # Exit price
    'target': float,            # Target price
    'stop_loss': float,         # Stop loss price
    'exit_reason': str,         # Why trade exited
    'target_hit': bool,         # Whether target was reached
    'stop_hit': bool,           # Whether stop was hit
    # Strategy-specific fields...
}
```

### Backtesting Engine Integration

The `StrategyManager` class orchestrates all strategies:

```python
def run_all_strategies(self, ticker, data):
    all_signals = []

    for strategy in self.strategies:
        # Map strategy name to config key
        strategy_key = strategy.name.lower().replace(' ', '_')

        # Check if enabled
        if Config.STRATEGIES[strategy_key]['enabled']:
            signals = strategy.generate_signals(ticker, data)
            all_signals.extend(signals)

    return all_signals
```

### Performance Considerations

- **Vectorization**: Uses pandas operations where possible
- **Caching**: Stores fetched data to reduce API calls
- **Memory Management**: Processes one ticker at a time for large datasets
- **Error Handling**: Graceful fallbacks for missing data or API failures

---

## Strategy Effectiveness Notes

### Parameter Sensitivity

- **Gap thresholds**: Higher values = fewer but higher quality signals
- **Float limits**: Lower values = more volatile stocks
- **Volume requirements**: Higher values = better liquidity but fewer signals

### Market Conditions

- **Bull Markets**: Short strategies may underperform
- **Bear Markets**: Short strategies may outperform
- **High Volatility**: All strategies tend to perform better
- **Low Volatility**: Fewer signals generated

### Risk Considerations

- **Concentration Risk**: Don't risk too much on single trades
- **Market Risk**: Overall market direction affects all strategies
- **Liquidity Risk**: Ensure sufficient volume for entry/exit
- **Timing Risk**: Gap openings can be difficult to trade in reality

This implementation provides a solid foundation for backtesting these professional trading strategies with realistic entry/exit mechanics and proper risk management.
