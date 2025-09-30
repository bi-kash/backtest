# Trading Backtest Configuration
# This file contains all the parameters you can easily modify

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """
    Configuration class for trading strategies.
    
    Parameter Loading Priority:
    1. First checks for strategy_parameters_template.xlsx (user-friendly Excel modification)
    2. Falls back to hardcoded defaults in this file if Excel doesn't exist
    
    For actual backtesting, parameters are loaded in this order:
    - Excel file (strategy_parameters_template.xlsx) if it exists
    - config.py defaults if Excel file doesn't exist
    """
    # Polygon.io API Configuration
    POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "YOUR_POLYGON_API_KEY_HERE")
    
    # Strategy Parameters - Default Values (Easy to modify)
    # These are the hardcoded defaults used when Excel template doesn't exist
    DEFAULT_STRATEGIES = {
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
    
    # Active strategy parameters (will be loaded from Excel or defaults)
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
    
    @staticmethod
    def load_parameters_from_excel(filename='strategy_parameters_template.xlsx'):
        """
        Load strategy parameters from Excel file if it exists.
        This allows non-programmers to modify parameters in Excel.
        
        Returns:
            bool: True if parameters were loaded from Excel, False if using config.py defaults
        """
        import os
        
        if not os.path.exists(filename):
            print(f"Excel parameter file '{filename}' not found. Using config.py defaults.")
            return False
        
        try:
            import openpyxl
            
            # Use openpyxl directly to avoid pandas' bool/int conversion issues
            wb = openpyxl.load_workbook(filename)
            ws = wb['Parameters']
            
            # Parse the Excel structure into our STRATEGIES dict
            current_strategy = None
            warnings = []
            
            # Skip header row, start from row 2
            for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
                strategy_name, parameter_name, current_value, _, _ = row
                
                # When we see a strategy name, map it to our internal key
                if strategy_name:
                    # Convert "Gap Up Short" to "gap_up_short"
                    current_strategy = strategy_name.lower().replace(' ', '_')
                    
                    # Initialize strategy dict if needed
                    if current_strategy not in Config.STRATEGIES:
                        Config.STRATEGIES[current_strategy] = {}
                
                # Update the parameter for the current strategy
                if current_strategy and parameter_name:
                    # Convert "Min Gap Percent" to "min_gap_percent"
                    param_key = parameter_name.lower().replace(' ', '_')
                    
                    # Validate parameter value
                    if current_value is None:
                        warnings.append(f"Row {row_num}: {parameter_name} has no value, using default")
                        # Use default value
                        if current_strategy in Config.DEFAULT_STRATEGIES:
                            current_value = Config.DEFAULT_STRATEGIES[current_strategy].get(param_key)
                    
                    # Basic type validation for numeric parameters
                    if 'percent' in param_key or 'millions' in param_key or 'days' in param_key or 'ratio' in param_key:
                        if not isinstance(current_value, (int, float, bool)):
                            warnings.append(f"Row {row_num}: {parameter_name} should be numeric, got {type(current_value).__name__}")
                    
                    # Store the value with proper type
                    Config.STRATEGIES[current_strategy][param_key] = current_value
            
            print(f"✓ Parameters loaded from Excel file: {filename}")
            
            if warnings:
                print("\n⚠️  Warnings during parameter loading:")
                for warning in warnings[:5]:  # Show max 5 warnings
                    print(f"   • {warning}")
                if len(warnings) > 5:
                    print(f"   • ... and {len(warnings) - 5} more warnings")
            
            print("  To use config.py defaults instead, rename or delete the Excel file.")
            return True
            
        except Exception as e:
            print(f"Error loading parameters from Excel: {e}")
            print("Using config.py defaults instead.")
            return False
    
    @staticmethod
    def initialize():
        """
        Initialize configuration by loading parameters.
        Call this at startup to load from Excel if available.
        """
        Config.load_parameters_from_excel()


# Auto-load parameters from Excel if available when module is imported
# This ensures the most recent Excel parameters are always used
Config.initialize()