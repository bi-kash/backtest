import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config import Config

class TradingStrategy:
    """
    Base class for all trading strategies
    """
    
    def __init__(self, name):
        self.name = name
        self.signals = []
    
    def generate_signals(self, data):
        """
        Override this method in each strategy
        """
        raise NotImplementedError

class GapUpShortStrategy(TradingStrategy):
    """
    Gap Up Short Strategy:
    - Stock gaps up over 70% (configurable)
    - Target: Stock comes back down 50% (configurable)
    - Short bias trader strategy
    """
    
    def __init__(self):
        super().__init__("Gap Up Short")
        self.config = Config.STRATEGIES['gap_up_short']
    
    def generate_signals(self, ticker, data):
        signals = []
        
        for i in range(1, len(data)):
            current_day = data.iloc[i]
            previous_day = data.iloc[i-1]
            
            # Calculate gap percentage
            gap_percent = ((current_day['open'] - previous_day['close']) / previous_day['close']) * 100
            
            # Check if this is a gap up short setup
            if (gap_percent >= self.config['min_gap_percent'] and
                current_day['float_millions'] <= self.config['max_float_millions'] and
                current_day['volume_millions'] >= self.config['min_volume_millions']):
                
                # Entry: Short at open after gap up
                entry_price = current_day['open']
                
                # Target: 50% retrace of the gap
                gap_amount = current_day['open'] - previous_day['close']
                target_price = current_day['open'] - (gap_amount * self.config['target_retrace_percent'] / 100)
                
                # Stop loss: Previous day high or current day high
                stop_loss = max(previous_day['high'], current_day['high'])
                
                # Check if target was hit during the day
                exit_price = target_price if current_day['low'] <= target_price else current_day['close']
                
                # Calculate if stop was hit
                stop_hit = current_day['high'] >= stop_loss
                if stop_hit:
                    exit_price = stop_loss
                
                signal = {
                    'date': current_day['date'],
                    'ticker': ticker,
                    'setup_type': 'Gap Up Short',
                    'entry': entry_price,
                    'exit': exit_price,
                    'target': target_price,
                    'stop_loss': stop_loss,
                    'gap_percent': gap_percent,
                    'float_millions': current_day['float_millions'],
                    'volume_millions': current_day['volume_millions'],
                    'stop_hit': stop_hit,
                    'target_hit': current_day['low'] <= target_price
                }
                
                signals.append(signal)
        
        return signals

class FirstRedDayStrategy(TradingStrategy):
    """
    First Red Day Strategy:
    - One month of extended consistent green candles
    - Closes weak and failed morning spike
    - Look for first red day to short
    """
    
    def __init__(self):
        super().__init__("First Red Day")
        self.config = Config.STRATEGIES['first_red_day']
    
    def generate_signals(self, ticker, data):
        signals = []
        
        for i in range(self.config['min_green_days'], len(data)):
            current_day = data.iloc[i]
            
            # Check if current day is red (close < open)
            if current_day['close'] >= current_day['open']:
                continue
            
            # Check previous days for consecutive green candles
            green_days_count = 0
            for j in range(i - self.config['min_green_days'], i):
                if data.iloc[j]['close'] > data.iloc[j]['open']:
                    green_days_count += 1
                else:
                    break
            
            # Check if we have enough consecutive green days
            if (green_days_count >= self.config['min_green_days'] and
                current_day['float_millions'] <= self.config['max_float_millions'] and
                current_day['volume_millions'] >= self.config['min_volume_millions']):
                
                # Entry: Short at close of first red day
                entry_price = current_day['close']
                
                # Target: 20% down from entry (configurable)
                target_price = entry_price * 0.8
                
                # Stop loss: High of the day or previous day high
                previous_day = data.iloc[i-1]
                stop_loss = max(current_day['high'], previous_day['high'])
                
                # Look ahead to determine actual exit price
                exit_price = entry_price  # Default fallback
                exit_reason = 'timeout'
                target_hit = False
                stop_hit = False
                max_lookforward = 10  # Look up to 10 days ahead
                
                # Walk forward through subsequent bars to find exit
                for j in range(i + 1, min(i + 1 + max_lookforward, len(data))):
                    future_day = data.iloc[j]
                    
                    # Check if stop loss is hit (price goes above stop)
                    if future_day['high'] >= stop_loss:
                        exit_price = stop_loss
                        exit_reason = 'stop_loss'
                        stop_hit = True
                        break
                    
                    # Check if target is hit (price goes below target)
                    if future_day['low'] <= target_price:
                        exit_price = target_price
                        exit_reason = 'target'
                        target_hit = True
                        break
                    
                    # If neither hit, use the close of this day as potential exit
                    exit_price = future_day['close']
                    exit_reason = 'market_close'
                
                signal = {
                    'date': current_day['date'],
                    'ticker': ticker,
                    'setup_type': 'First Red Day',
                    'entry': entry_price,
                    'exit': exit_price,
                    'target': target_price,
                    'stop_loss': stop_loss,
                    'green_days_prior': green_days_count,
                    'float_millions': current_day['float_millions'],
                    'volume_millions': current_day['volume_millions'],
                    'exit_reason': exit_reason,
                    'target_hit': target_hit,
                    'stop_hit': stop_hit
                }
                
                signals.append(signal)
        
        return signals

class ExtendedGapDownStrategy(TradingStrategy):
    """
    Extended Gap Down Strategy:
    - Stock is trading down 5%+ from previous close
    - Use previous open or previous day high as cover position
    """
    
    def __init__(self):
        super().__init__("Extended Gap Down")
        self.config = Config.STRATEGIES['extended_gap_down']
    
    def generate_signals(self, ticker, data):
        signals = []
        
        for i in range(1, len(data)):
            current_day = data.iloc[i]
            previous_day = data.iloc[i-1]
            
            # Calculate gap down percentage
            gap_percent = ((current_day['open'] - previous_day['close']) / previous_day['close']) * 100
            
            # Check if this is an extended gap down setup
            if (gap_percent <= -self.config['min_gap_down_percent'] and
                current_day['float_millions'] <= self.config['max_float_millions'] and
                current_day['volume_millions'] >= self.config['min_volume_millions']):
                
                # Entry: Short when stock gaps down 5%+
                entry_price = current_day['open']
                
                # Target: Continue down (use 10% more down as target)
                target_price = entry_price * 0.9
                
                # Stop loss: Previous day open or high
                stop_loss = max(previous_day['open'], previous_day['high'])
                
                # Look ahead to determine actual exit price
                exit_price = entry_price  # Default fallback
                exit_reason = 'timeout'
                target_hit = False
                stop_hit = False
                max_lookforward = 10  # Look up to 10 days ahead
                
                # Check if target hit same day first
                if current_day['low'] <= target_price:
                    exit_price = target_price
                    exit_reason = 'target'
                    target_hit = True
                elif current_day['high'] >= stop_loss:
                    exit_price = stop_loss
                    exit_reason = 'stop_loss'
                    stop_hit = True
                else:
                    # Walk forward through subsequent bars to find exit
                    for j in range(i + 1, min(i + 1 + max_lookforward, len(data))):
                        future_day = data.iloc[j]
                        
                        # Check if stop loss is hit (price goes above stop)
                        if future_day['high'] >= stop_loss:
                            exit_price = stop_loss
                            exit_reason = 'stop_loss'
                            stop_hit = True
                            break
                        
                        # Check if target is hit (price goes below target)
                        if future_day['low'] <= target_price:
                            exit_price = target_price
                            exit_reason = 'target'
                            target_hit = True
                            break
                        
                        # If neither hit, use the close of this day as potential exit
                        exit_price = future_day['close']
                        exit_reason = 'market_close'
                
                signal = {
                    'date': current_day['date'],
                    'ticker': ticker,
                    'setup_type': 'Extended Gap Down',
                    'entry': entry_price,
                    'exit': exit_price,
                    'target': target_price,
                    'stop_loss': stop_loss,
                    'gap_percent': gap_percent,
                    'float_millions': current_day['float_millions'],
                    'volume_millions': current_day['volume_millions'],
                    'exit_reason': exit_reason,
                    'target_hit': target_hit,
                    'stop_hit': stop_hit
                }
                
                signals.append(signal)
        
        return signals

class GapFillCloseStrategy(TradingStrategy):
    """
    Gap Fill Close Strategy (Long Strategy):
    - Stock gaps up over 100%
    - Closes above or around opening price
    - Go long at 3:59 PM, sell next day
    """
    
    def __init__(self):
        super().__init__("Gap Fill Close")
        self.config = Config.STRATEGIES['gap_fill_close']
    
    def generate_signals(self, ticker, data):
        signals = []
        
        for i in range(1, len(data) - 1):  # -1 because we need next day data
            current_day = data.iloc[i]
            previous_day = data.iloc[i-1]
            next_day = data.iloc[i+1]
            
            # Calculate gap percentage
            gap_percent = ((current_day['open'] - previous_day['close']) / previous_day['close']) * 100
            
            # Check if stock closes above or near opening price
            close_vs_open_ratio = current_day['close'] / current_day['open']
            
            # Check if this is a gap fill close setup
            if (gap_percent >= self.config['min_gap_percent'] and
                close_vs_open_ratio >= 0.95 and  # Closes within 5% of open
                current_day['volume_millions'] >= self.config['min_volume_millions']):
                
                # Entry: Long at 3:59 PM (use close price as approximation)
                entry_price = current_day['close']
                
                # Exit: Next day (sell at open or close, use close for safety)
                exit_price = next_day['close']
                
                # Target and stop loss for long position
                target_price = entry_price * 1.1  # 10% target
                stop_loss = entry_price * 0.95    # 5% stop loss
                
                signal = {
                    'date': current_day['date'],
                    'ticker': ticker,
                    'setup_type': 'Gap Fill Close (Long)',
                    'entry': entry_price,
                    'exit': exit_price,
                    'target': target_price,
                    'stop_loss': stop_loss,
                    'gap_percent': gap_percent,
                    'close_vs_open_ratio': close_vs_open_ratio,
                    'volume_millions': current_day['volume_millions']
                }
                
                signals.append(signal)
        
        return signals

class MultiDayBreakoutStrategy(TradingStrategy):
    """
    Multi-day Breakout Strategy:
    - Weekly breakout with heavy volume in morning
    - Look for volume spike vs average volume
    """
    
    def __init__(self):
        super().__init__("Multi Day Breakout")
        self.config = Config.STRATEGIES['multi_day_breakout']
    
    def generate_signals(self, ticker, data):
        signals = []
        
        # Calculate average volume over the period
        data['avg_volume_5d'] = data['volume'].rolling(window=5, min_periods=1).mean()
        
        for i in range(5, len(data)):  # Need 5 days of history
            current_day = data.iloc[i]
            
            # Check for volume breakout (volume > 2x average volume)
            volume_ratio = current_day['volume'] / current_day['avg_volume_5d']
            
            # Check for price breakout (high > highest high of last 5 days)
            recent_highs = data.iloc[i-5:i]['high']
            is_price_breakout = current_day['high'] > recent_highs.max()
            
            # Check if this is a multi-day breakout setup
            if (volume_ratio >= self.config['min_volume_ratio'] and
                is_price_breakout and
                current_day['volume_millions'] >= self.config['min_volume_millions']):
                
                # Entry: Long at breakout level (use high of day)
                entry_price = current_day['high']
                
                # Target: 15% above entry
                target_price = entry_price * 1.15
                
                # Stop loss: Low of the day or previous support
                stop_loss = current_day['low']
                
                # Look ahead to determine actual exit price (Long position)
                exit_price = entry_price  # Default fallback
                exit_reason = 'timeout'
                target_hit = False
                stop_hit = False
                max_lookforward = 10  # Look up to 10 days ahead
                
                # Check if target or stop hit same day first
                if current_day['high'] >= target_price:
                    exit_price = target_price
                    exit_reason = 'target'
                    target_hit = True
                elif current_day['low'] < stop_loss:
                    exit_price = stop_loss
                    exit_reason = 'stop_loss'
                    stop_hit = True
                else:
                    # Walk forward through subsequent bars to find exit
                    for j in range(i + 1, min(i + 1 + max_lookforward, len(data))):
                        future_day = data.iloc[j]
                        
                        # Check if target is hit (price goes above target for long)
                        if future_day['high'] >= target_price:
                            exit_price = target_price
                            exit_reason = 'target'
                            target_hit = True
                            break
                        
                        # Check if stop loss is hit (price goes below stop for long)
                        if future_day['low'] <= stop_loss:
                            exit_price = stop_loss
                            exit_reason = 'stop_loss'
                            stop_hit = True
                            break
                        
                        # If neither hit, use the close of this day as potential exit
                        exit_price = future_day['close']
                        exit_reason = 'market_close'
                
                signal = {
                    'date': current_day['date'],
                    'ticker': ticker,
                    'setup_type': 'Multi Day Breakout',
                    'entry': entry_price,
                    'exit': exit_price,
                    'target': target_price,
                    'stop_loss': stop_loss,
                    'volume_ratio': volume_ratio,
                    'volume_millions': current_day['volume_millions'],
                    'exit_reason': exit_reason,
                    'target_hit': target_hit,
                    'stop_hit': stop_hit
                }
                
                signals.append(signal)
        
        return signals

class StrategyManager:
    """
    Manages all trading strategies and applies them to data
    """
    
    def __init__(self):
        self.strategies = [
            GapUpShortStrategy(),
            FirstRedDayStrategy(),
            ExtendedGapDownStrategy(),
            GapFillCloseStrategy(),
            MultiDayBreakoutStrategy()
        ]
    
    def run_all_strategies(self, ticker, data):
        """
        Run all enabled strategies on the given data
        """
        all_signals = []
        
        for strategy in self.strategies:
            # Check if strategy is enabled in config
            strategy_key = strategy.name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('_long', '')
            
            if strategy_key in Config.STRATEGIES and Config.STRATEGIES[strategy_key]['enabled']:
                signals = strategy.generate_signals(ticker, data)
                all_signals.extend(signals)
        
        return all_signals
    
    def get_strategy_by_name(self, name):
        """
        Get a specific strategy by name
        """
        for strategy in self.strategies:
            if strategy.name == name:
                return strategy
        return None