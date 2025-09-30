# Trading Backtest System - Main Entry Point
# Easy-to-use interface for running backtests

import sys
import os
from datetime import datetime, timedelta
from backtest_engine import BacktestEngine
from config import Config

def print_menu():
    """Print the main menu"""
    print("\n" + "="*50)
    print("TRADING STRATEGY BACKTESTING SYSTEM")
    print("="*50)
    print("1. Run Full Backtest (All Strategies)")
    print("2. Test Single Stock")
    print("3. Optimize Strategy Parameters")
    print("4. View/Edit Configuration")
    print("5. Create Parameter Template")
    print("6. Quick Test (Last 30 Days)")
    print("7. Exit")
    print("="*50)

def get_ticker_list():
    """Get list of tickers from user"""
    print("\nEnter stock tickers (comma-separated):")
    print("Example: AAPL,MSFT,TSLA,AMC,GME")
    print("Or press Enter for default list...")
    
    user_input = input().strip()
    
    if not user_input:
        # Default list focused on volatile stocks good for your strategies
        default_tickers = [
            'AMC', 'GME', 'BBBY', 'SPRT', 'IRNT', 'OPAD', 
            'DWAC', 'PHUN', 'BKKT', 'PROG', 'ATER', 'BBIG'
        ]
        print(f"Using default tickers: {', '.join(default_tickers)}")
        return default_tickers
    
    return [ticker.strip().upper() for ticker in user_input.split(',')]

def get_date_range():
    """Get date range from user"""
    print("\nDate Range:")
    print("1. Last 30 days")
    print("2. Last 3 months") 
    print("3. Last 6 months")
    print("4. Custom range")
    print("5. Use config settings")
    
    choice = input("Select option (1-5): ").strip()
    
    today = datetime.now()
    
    if choice == '1':
        start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    elif choice == '2':
        start_date = (today - timedelta(days=90)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    elif choice == '3':
        start_date = (today - timedelta(days=180)).strftime('%Y-%m-%d')
        end_date = today.strftime('%Y-%m-%d')
    elif choice == '4':
        start_date = input("Start date (YYYY-MM-DD): ").strip()
        end_date = input("End date (YYYY-MM-DD): ").strip()
    else:
        start_date = Config.BACKTEST_SETTINGS['start_date']
        end_date = Config.BACKTEST_SETTINGS['end_date']
    
    return start_date, end_date

def run_full_backtest():
    """Run full backtest on multiple tickers"""
    print("\n--- FULL BACKTEST ---")
    
    tickers = get_ticker_list()
    start_date, end_date = get_date_range()
    
    print(f"\nRunning backtest on {len(tickers)} tickers from {start_date} to {end_date}")
    print("This may take a few minutes...")
    
    engine = BacktestEngine()
    signals = engine.run_backtest(tickers, start_date, end_date)
    
    if signals:
        print(f"\nBacktest completed! Found {len(signals)} trading opportunities.")
        print("Results have been exported to Excel.")
    else:
        print("\nNo trading signals found. Try:")
        print("1. Different tickers")
        print("2. Longer date range") 
        print("3. Adjusting strategy parameters in config.py")

def test_single_stock():
    """Test a single stock in detail"""
    print("\n--- SINGLE STOCK ANALYSIS ---")
    
    ticker = input("Enter ticker symbol: ").strip().upper()
    start_date, end_date = get_date_range()
    
    engine = BacktestEngine()
    signals, data = engine.run_single_ticker_analysis(ticker, start_date, end_date)
    
    if signals:
        print(f"\nAnalysis complete for {ticker}!")
        
        # Export single ticker results
        filename = f"{ticker}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        engine.excel_generator.export_to_excel(signals, filename)
        print(f"Detailed results exported to {filename}")
    else:
        print(f"\nNo trading opportunities found for {ticker}")

def optimize_parameters():
    """Optimize strategy parameters"""
    print("\n--- PARAMETER OPTIMIZATION ---")
    
    ticker = input("Enter ticker for optimization: ").strip().upper()
    
    print("\nAvailable strategies:")
    print("1. Gap Up Short")
    print("2. First Red Day")
    print("3. Extended Gap Down")
    print("4. Gap Fill Close")
    print("5. Multi Day Breakout")
    
    strategy_choice = input("Select strategy (1-5): ").strip()
    
    strategy_map = {
        '1': 'Gap Up Short',
        '2': 'First Red Day', 
        '3': 'Extended Gap Down',
        '4': 'Gap Fill Close',
        '5': 'Multi Day Breakout'
    }
    
    if strategy_choice not in strategy_map:
        print("Invalid choice!")
        return
    
    strategy_name = strategy_map[strategy_choice]
    
    # Example parameter ranges (you can modify these)
    if strategy_name == 'Gap Up Short':
        parameter_ranges = {
            'min_gap_percent': [50, 70, 100, 150],
            'target_retrace_percent': [30, 40, 50, 60],
            'max_float_millions': [20, 50, 100]
        }
    else:
        print("Parameter optimization for this strategy is not implemented yet.")
        return
    
    engine = BacktestEngine()
    best_params, results = engine.optimize_strategy_parameters(ticker, strategy_name, parameter_ranges)
    
    print(f"\nOptimization results:")
    print(f"Best parameters for {strategy_name}: {best_params}")

def view_configuration():
    """Display current configuration"""
    print("\n--- CURRENT CONFIGURATION ---")
    
    print("\nSTRATEGY SETTINGS:")
    for strategy, params in Config.STRATEGIES.items():
        print(f"\n{strategy.replace('_', ' ').title()}:")
        for param, value in params.items():
            print(f"  {param}: {value}")
    
    print("\nRISK MANAGEMENT:")
    for param, value in Config.RISK_MANAGEMENT.items():
        print(f"  {param}: {value}")
    
    print("\nBACKTEST SETTINGS:")
    for param, value in Config.BACKTEST_SETTINGS.items():
        print(f"  {param}: {value}")
    
    print("\nTo modify these settings, edit config.py")

def create_template():
    """Create parameter template"""
    print("\n--- CREATING PARAMETER TEMPLATE ---")
    
    from excel_export import ExcelReportGenerator
    generator = ExcelReportGenerator()
    filename = generator.create_parameter_template()
    
    print(f"\nParameter template created: {filename}")
    print("\n📌 IMPORTANT: How parameters are used for backtesting:")
    print("  1. If Excel template exists: Parameters are loaded FROM EXCEL")
    print("  2. If Excel template doesn't exist: Parameters are loaded from config.py")
    print("\nTo modify parameters:")
    print("  • Open the Excel file and change 'Current Value' column")
    print("  • Save the file")
    print("  • Restart the program (parameters are loaded at startup)")
    print("\nSee PARAMETER_LOADING.md for complete details.")

def quick_test():
    """Quick test with recent volatile stocks"""
    print("\n--- QUICK TEST (Last 30 Days) ---")
    
    # Pre-selected volatile tickers that often have the patterns you're looking for
    volatile_tickers = ['AMC', 'GME', 'SPRT', 'IRNT', 'OPAD', 'DWAC']
    
    today = datetime.now()
    start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
    end_date = today.strftime('%Y-%m-%d')
    
    print(f"Testing {', '.join(volatile_tickers)} from {start_date} to {end_date}")
    
    engine = BacktestEngine()
    signals = engine.run_backtest(volatile_tickers, start_date, end_date)
    
    if signals:
        print(f"\nQuick test completed! Found {len(signals)} opportunities.")
    else:
        print("\nNo signals found in recent data.")

def check_setup():
    """Check if system is properly configured"""
    issues = []
    
    # Check API key
    if Config.POLYGON_API_KEY == "YOUR_POLYGON_API_KEY_HERE":
        issues.append("Polygon.io API key not configured in .env file")
    
    # Check required packages
    try:
        import pandas, requests, openpyxl, polygon
        from polygon import RESTClient
    except ImportError as e:
        issues.append(f"Missing package: {e}")
    
    if issues:
        print("\nSETUP ISSUES DETECTED:")
        for issue in issues:
            print(f"- {issue}")
        print("\nPlease fix these issues before running backtests.")
        return False
    else:
        print("\nSystem setup looks good!")
        return True

def main():
    """Main program loop"""
    print("Welcome to the Trading Strategy Backtesting System!")
    
    # Check setup
    if not check_setup():
        print("\nSetup incomplete. Please fix the issues above.")
        return
    
    while True:
        print_menu()
        choice = input("\nSelect option (1-7): ").strip()
        
        try:
            if choice == '1':
                run_full_backtest()
            elif choice == '2':
                test_single_stock()
            elif choice == '3':
                optimize_parameters()
            elif choice == '4':
                view_configuration()
            elif choice == '5':
                create_template()
            elif choice == '6':
                quick_test()
            elif choice == '7':
                print("Thank you for using the Trading Backtest System!")
                break
            else:
                print("Invalid option! Please select 1-7.")
        
        except KeyboardInterrupt:
            print("\n\nProgram interrupted by user.")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            print("Please check your inputs and try again.")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    main()