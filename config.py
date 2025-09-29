# Trading Backtest Configuration
# This file contains all the parameters you can easily modify

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Polygon.io API Configuration
    POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "YOUR_POLYGON_API_KEY_HERE")
    
    # Strategy Parameters (Easy to modify)
    STRATEGIES = {
        'gap_up_short': {
            'enabled': True,
            'min_gap_percent': 70,  # Minimum gap up percentage
            'target_retrace_percent': 50,  # Target retrace for profit
            'max_float_millions': 50,  # Maximum float in millions
            'min_volume_millions': 1,  # Minimum volume in millions
        },
        'first_red_day': {
            'enabled': True,
            'min_green_days': 20,  # Minimum consecutive green days before
            'max_float_millions': 100,
            'min_volume_millions': 2,
        },
        'extended_gap_down': {
            'enabled': True,
            'min_gap_down_percent': 5,  # Minimum gap down percentage
            'max_float_millions': 200,
            'min_volume_millions': 1,
        },
        'gap_fill_close': {
            'enabled': True,
            'min_gap_percent': 100,  # Minimum gap up percentage
            'entry_time': '15:59',  # Entry time (3:59 PM)
            'min_volume_millions': 1,
        },
        'multi_day_breakout': {
            'enabled': True,
            'min_volume_ratio': 2,  # Volume vs average volume ratio
            'min_volume_millions': 5,
            'breakout_period_days': 5,
        }
    }
    
    # Risk Management
    RISK_MANAGEMENT = {
        'max_risk_per_trade': 1000,  # Maximum $ risk per trade
        'stop_loss_percent': 10,     # Stop loss percentage
        'position_size_method': 'fixed_dollar',  # 'fixed_dollar' or 'percent_portfolio'
        'fixed_dollar_amount': 10000,  # Fixed dollar amount per trade
    }
    
    # Backtesting Parameters
    BACKTEST_SETTINGS = {
        'start_date': '2024-01-01',
        'end_date': '2024-12-31',
        'commission_per_share': 0.005,  # Commission per share
        'slippage_percent': 0.1,        # Slippage percentage
    }
    
    # Excel Output Settings
    EXCEL_SETTINGS = {
        'output_filename': 'backtest_results.xlsx',
        'include_charts': True,
        'auto_format': True,
    }