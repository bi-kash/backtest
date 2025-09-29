import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from data_fetcher import PolygonDataFetcher
from strategies import StrategyManager
from excel_export import ExcelReportGenerator
from config import Config

class BacktestEngine:
    """
    Main backtesting engine that orchestrates data fetching, strategy execution, and reporting
    """
    
    def __init__(self, api_key=None):
        self.data_fetcher = PolygonDataFetcher(api_key)
        self.strategy_manager = StrategyManager()
        self.excel_generator = ExcelReportGenerator()
        self.results = []
    
    def run_backtest(self, tickers, start_date=None, end_date=None):
        """
        Run complete backtest on list of tickers
        
        Args:
            tickers: List of stock tickers to test
            start_date: Start date for backtest (YYYY-MM-DD)
            end_date: End date for backtest (YYYY-MM-DD)
        """
        # Use config dates if not provided
        start_date = start_date or Config.BACKTEST_SETTINGS['start_date']
        end_date = end_date or Config.BACKTEST_SETTINGS['end_date']
        
        print(f"Starting backtest from {start_date} to {end_date}")
        print(f"Testing {len(tickers)} tickers...")
        
        all_signals = []
        
        # Get historical data for all tickers
        print("Fetching historical data...")
        historical_data = self.data_fetcher.get_historical_data_batch(tickers, start_date, end_date)
        
        # Run strategies on each ticker
        for ticker, data in historical_data.items():
            if data.empty:
                continue
                
            print(f"Running strategies on {ticker}...")
            
            # Add dollar block calculation for each day
            for i in range(len(data)):
                if i >= 5:  # Need at least 5 days for consolidation
                    consolidation_data = data.iloc[i-4:i+1]
                    data.loc[data.index[i], 'dollar_block'] = self.data_fetcher.calculate_dollar_block(consolidation_data)
            
            # Run all strategies
            signals = self.strategy_manager.run_all_strategies(ticker, data)
            
            # Add dollar block and rotation to each signal
            for signal in signals:
                signal_date = signal['date']
                matching_row = data[data['date'] == signal_date]
                if not matching_row.empty:
                    signal['dollar_block'] = matching_row.iloc[0].get('dollar_block', 0)
                    signal['rotation'] = matching_row.iloc[0].get('rotation', 0)
            
            all_signals.extend(signals)
        
        print(f"Generated {len(all_signals)} trading signals")
        
        # Generate Excel report
        if all_signals:
            filename = self.excel_generator.export_to_excel(all_signals)
            print(f"Results exported to {filename}")
            
            # Generate summary statistics
            self.print_summary_stats(all_signals)
        else:
            print("No trading signals generated. Try adjusting strategy parameters.")
        
        self.results = all_signals
        return all_signals
    
    def print_summary_stats(self, signals):
        """
        Print summary statistics to console
        """
        if not signals:
            return
        
        # Convert to DataFrame for analysis
        trades_df = self.excel_generator.create_trades_dataframe(signals)
        
        print("\n" + "="*50)
        print("BACKTEST SUMMARY")
        print("="*50)
        
        total_trades = len(trades_df)
        winning_trades = len(trades_df[trades_df['Win/Loss'] == 'Win'])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = trades_df['P&L ($)'].sum()
        avg_win = trades_df[trades_df['Win/Loss'] == 'Win']['P&L ($)'].mean() if winning_trades > 0 else 0
        avg_loss = trades_df[trades_df['Win/Loss'] == 'Loss']['P&L ($)'].mean() if len(trades_df[trades_df['Win/Loss'] == 'Loss']) > 0 else 0
        
        print(f"Total Trades: {total_trades}")
        print(f"Winning Trades: {winning_trades}")
        print(f"Win Rate: {win_rate:.2f}%")
        print(f"Total P&L: ${total_pnl:,.2f}")
        print(f"Average Win: ${avg_win:,.2f}")
        print(f"Average Loss: ${avg_loss:,.2f}")
        
        print("\nStrategy Breakdown:")
        strategy_stats = trades_df.groupby('Setup Type').agg({
            'P&L ($)': ['count', 'sum'],
            'Win/Loss': lambda x: (x == 'Win').sum() / len(x) * 100
        }).round(2)
        
        for strategy in strategy_stats.index:
            count = strategy_stats.loc[strategy, ('P&L ($)', 'count')]
            pnl = strategy_stats.loc[strategy, ('P&L ($)', 'sum')]
            win_rate = strategy_stats.loc[strategy, ('Win/Loss', '<lambda>')]
            print(f"  {strategy}: {count} trades, ${pnl:,.2f} P&L, {win_rate:.1f}% win rate")
        
        print("="*50)
    
    def run_single_ticker_analysis(self, ticker, start_date=None, end_date=None):
        """
        Run detailed analysis on a single ticker
        """
        start_date = start_date or Config.BACKTEST_SETTINGS['start_date']
        end_date = end_date or Config.BACKTEST_SETTINGS['end_date']
        
        print(f"Analyzing {ticker} from {start_date} to {end_date}")
        
        # Get data
        data = self.data_fetcher.get_stock_data(ticker, start_date, end_date)
        
        if data.empty:
            print(f"No data available for {ticker}")
            return
        
        # Add additional metrics
        float_info = self.data_fetcher.get_float_data(ticker)
        data['float_millions'] = float_info['float_millions']
        data['volume_millions'] = data['volume'] / 1_000_000
        data['rotation'] = data['volume_millions'] / data['float_millions'] if data['float_millions'].iloc[0] > 0 else 0
        
        # Calculate gaps and dollar blocks
        data['gap_percent'] = 0.0
        data['dollar_block'] = 0.0
        
        for i in range(1, len(data)):
            data.loc[data.index[i], 'gap_percent'] = self.data_fetcher.calculate_gap_percentage(
                data.iloc[i]['open'], 
                data.iloc[i-1]['close']
            )
            
            if i >= 5:
                consolidation_data = data.iloc[i-4:i+1]
                data.loc[data.index[i], 'dollar_block'] = self.data_fetcher.calculate_dollar_block(consolidation_data)
        
        # Run strategies
        signals = self.strategy_manager.run_all_strategies(ticker, data)
        
        print(f"Found {len(signals)} trading opportunities")
        
        # Print details of each signal
        for i, signal in enumerate(signals, 1):
            print(f"\nSignal {i}: {signal['setup_type']}")
            print(f"  Date: {signal['date']}")
            print(f"  Entry: ${signal['entry']:.2f}")
            print(f"  Exit: ${signal['exit']:.2f}")
            print(f"  Gap: {signal.get('gap_percent', 0):.1f}%")
            print(f"  Volume: {signal.get('volume_millions', 0):.2f}M")
            print(f"  Float: {signal.get('float_millions', 0):.2f}M")
        
        return signals, data
    
    def optimize_strategy_parameters(self, ticker, strategy_name, parameter_ranges):
        """
        Run parameter optimization for a specific strategy
        
        Args:
            ticker: Stock ticker to optimize on
            strategy_name: Name of strategy to optimize
            parameter_ranges: Dict of parameter names and ranges to test
        """
        print(f"Optimizing {strategy_name} strategy on {ticker}")
        
        best_params = None
        best_score = float('-inf')
        results = []
        
        # Get base data
        data = self.data_fetcher.get_stock_data(ticker, Config.BACKTEST_SETTINGS['start_date'], Config.BACKTEST_SETTINGS['end_date'])
        
        if data.empty:
            print(f"No data available for {ticker}")
            return
        
        # Add required columns
        float_info = self.data_fetcher.get_float_data(ticker)
        data['float_millions'] = float_info['float_millions']
        data['volume_millions'] = data['volume'] / 1_000_000
        
        # Generate parameter combinations to test
        param_combinations = self._generate_parameter_combinations(parameter_ranges)
        
        for i, params in enumerate(param_combinations):
            print(f"Testing combination {i+1}/{len(param_combinations)}: {params}")
            
            # Update config temporarily
            original_config = Config.STRATEGIES[strategy_name.lower().replace(' ', '_')].copy()
            Config.STRATEGIES[strategy_name.lower().replace(' ', '_')].update(params)
            
            # Run strategy
            # Rebuild the strategy so it reflects the updated config params
            self.strategy_manager = StrategyManager()
            strategy = self.strategy_manager.get_strategy_by_name(strategy_name)
            if strategy:
                signals = strategy.generate_signals(ticker, data)
                
                # Calculate performance score
                if signals:
                    trades_df = self.excel_generator.create_trades_dataframe(signals)
                    score = self._calculate_optimization_score(trades_df)
                    
                    results.append({
                        'params': params.copy(),
                        'signals': len(signals),
                        'win_rate': (trades_df['Win/Loss'] == 'Win').sum() / len(trades_df) * 100 if len(trades_df) > 0 else 0,
                        'total_pnl': trades_df['P&L ($)'].sum() if len(trades_df) > 0 else 0,
                        'score': score
                    })
                    
                    if score > best_score:
                        best_score = score
                        best_params = params.copy()
            
            # Restore original config
            Config.STRATEGIES[strategy_name.lower().replace(' ', '_')] = original_config
        print(f"\nOptimization complete!")
        print(f"Best parameters: {best_params}")
        print(f"Best score: {best_score:.2f}")
        
        return best_params, results
    
    def _generate_parameter_combinations(self, parameter_ranges):
        """
        Generate all combinations of parameters to test
        """
        import itertools
        
        param_names = list(parameter_ranges.keys())
        param_values = [parameter_ranges[name] for name in param_names]
        
        combinations = []
        for combo in itertools.product(*param_values):
            combinations.append(dict(zip(param_names, combo)))
        
        return combinations[:20]  # Limit to 20 combinations to avoid long runtime
    
    def _calculate_optimization_score(self, trades_df):
        """
        Calculate optimization score based on multiple factors
        """
        if len(trades_df) == 0:
            return 0
        
        win_rate = (trades_df['Win/Loss'] == 'Win').sum() / len(trades_df)
        total_pnl = trades_df['P&L ($)'].sum()
        num_trades = len(trades_df)
        
        # Composite score: prioritize win rate and total PnL, with bonus for more trades
        score = (win_rate * 50) + (total_pnl / 100) + (num_trades * 0.1)
        
        return score

def main():
    """
    Main function to run the backtesting system
    """
    print("Trading Strategy Backtesting System")
    print("="*40)
    
    # Initialize backtest engine
    engine = BacktestEngine()
    
    # Example tickers (you can modify this list)
    # Focus on stocks that typically have the characteristics you're looking for
    tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA',  # Large caps (for comparison)
        'AMC', 'GME', 'BB', 'NKLA', 'PLTR',        # Meme stocks (high volatility)
        'SPRT', 'IRNT', 'OPAD', 'ANY', 'DWAC'      # Recent high flyers
    ]
    
    print(f"Testing with tickers: {', '.join(tickers)}")
    print("\nTo modify strategy parameters, edit config.py")
    print("To add your Polygon.io API key, create a .env file with POLYGON_API_KEY=your_key_here\n")
    
    # Run backtest
    signals = engine.run_backtest(tickers)
    
    # Create parameter template for easy modification
    engine.excel_generator.create_parameter_template()
    
    print("\nBacktest complete!")
    print("Check the generated Excel files for detailed results.")

if __name__ == "__main__":
    main()