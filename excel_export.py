import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.chart import BarChart, PieChart, Reference
import os
from datetime import datetime
from config import Config

class ExcelReportGenerator:
    """
    Handles Excel report generation with user-friendly formatting
    """
    
    def __init__(self):
        self.workbook = None
        self.filename = Config.EXCEL_SETTINGS['output_filename']
    
    def create_trades_dataframe(self, all_signals):
        """
        Convert trading signals to the specified DataFrame format
        """
        trades_data = []
        
        for signal in all_signals:
            # Calculate shares based on fixed dollar amount or risk management
            risk_amount = Config.RISK_MANAGEMENT['max_risk_per_trade']
            entry_price = signal['entry']
            stop_loss = signal.get('stop_loss', entry_price * 1.1)  # Default 10% stop if not provided
            
            # Calculate shares based on risk
            risk_per_share = abs(entry_price - stop_loss)
            shares = int(risk_amount / risk_per_share) if risk_per_share > 0 else 100
            
            # Calculate P&L
            exit_price = signal['exit']
            
            # Determine if it's a long or short position based on setup type
            is_short = 'short' in signal['setup_type'].lower() or 'gap down' in signal['setup_type'].lower()
            
            if is_short:
                pnl_dollars = shares * (entry_price - exit_price)
            else:
                pnl_dollars = shares * (exit_price - entry_price)
            
            # Subtract commission
            commission = shares * Config.BACKTEST_SETTINGS['commission_per_share'] * 2  # Entry + Exit
            pnl_dollars -= commission
            
            pnl_percent = (pnl_dollars / (shares * entry_price)) * 100 if entry_price > 0 else 0
            
            # Determine win/loss
            win_loss = 'Win' if pnl_dollars > 0 else 'Loss'
            
            # Setup quality (simplified scoring based on multiple factors)
            setup_quality = self.calculate_setup_quality(signal)
            
            # Pattern notes
            pattern_notes = self.generate_pattern_notes(signal)
            
            trade_data = {
                'Date': signal['date'],
                'Ticker': signal['ticker'],
                'Setup Type': signal['setup_type'],
                'Entry': round(entry_price, 2),
                'Exit': round(exit_price, 2),
                'Shares': shares,
                'P&L ($)': round(pnl_dollars, 2),
                'P&L (%)': round(pnl_percent, 2),
                'Win/Loss': win_loss,
                'Risk ($)': risk_amount,
                'Float (M)': round(signal.get('float_millions', 0), 2),
                'Vol (M)': round(signal.get('volume_millions', 0), 2),
                'Rotation': round(signal.get('rotation', signal.get('volume_millions', 0) / signal.get('float_millions', 1) if signal.get('float_millions', 0) > 0 else 0), 2),
                'Setup Quality': setup_quality,
                'Mistake Tag': '',  # Can be filled manually
                'Pattern Notes': pattern_notes,
                'Gap %': round(signal.get('gap_percent', 0), 2),
                'Dollar Block': round(signal.get('dollar_block', 0), 0),
                'Target Hit': signal.get('target_hit', False),
                'Stop Hit': signal.get('stop_hit', False)
            }
            
            trades_data.append(trade_data)
        
        return pd.DataFrame(trades_data)
    
    def calculate_setup_quality(self, signal):
        """
        Calculate setup quality score (1-10 scale)
        """
        score = 5  # Base score
        
        # Volume factor
        if signal.get('volume_millions', 0) > 5:
            score += 1
        elif signal.get('volume_millions', 0) > 10:
            score += 2
        
        # Float factor (lower is better for volatility)
        if signal.get('float_millions', 0) < 10:
            score += 1
        elif signal.get('float_millions', 0) < 5:
            score += 2
        
        # Gap percentage factor
        gap_percent = abs(signal.get('gap_percent', 0))
        if gap_percent > 50:
            score += 1
        if gap_percent > 100:
            score += 1
        
        # Volume ratio factor
        if signal.get('volume_ratio', 0) > 3:
            score += 1
        
        return min(10, max(1, score))
    
    def generate_pattern_notes(self, signal):
        """
        Generate descriptive pattern notes
        """
        notes = []
        
        setup_type = signal['setup_type']
        
        if 'Gap Up Short' in setup_type:
            notes.append(f"Gapped up {signal.get('gap_percent', 0):.1f}%")
            if signal.get('target_hit', False):
                notes.append("Hit target")
            if signal.get('stop_hit', False):
                notes.append("Stop hit")
        
        elif 'First Red Day' in setup_type:
            notes.append(f"After {signal.get('green_days_prior', 0)} green days")
        
        elif 'Gap Fill Close' in setup_type:
            notes.append(f"Gap up {signal.get('gap_percent', 0):.1f}%, closed near open")
        
        elif 'Multi Day Breakout' in setup_type:
            notes.append(f"Volume ratio: {signal.get('volume_ratio', 0):.1f}x")
        
        # Add float and volume info
        if signal.get('float_millions', 0) > 0:
            notes.append(f"Float: {signal.get('float_millions', 0):.1f}M")
        
        return "; ".join(notes)
    
    def create_summary_stats(self, df):
        """
        Create summary statistics
        """
        total_trades = len(df)
        winning_trades = len(df[df['Win/Loss'] == 'Win'])
        losing_trades = len(df[df['Win/Loss'] == 'Loss'])
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = df['P&L ($)'].sum()
        avg_win = df[df['Win/Loss'] == 'Win']['P&L ($)'].mean() if winning_trades > 0 else 0
        avg_loss = df[df['Win/Loss'] == 'Loss']['P&L ($)'].mean() if losing_trades > 0 else 0
        
        profit_factor = abs(avg_win * winning_trades / (avg_loss * losing_trades)) if avg_loss != 0 and losing_trades > 0 else float('inf')
        
        summary = {
            'Total Trades': total_trades,
            'Winning Trades': winning_trades,
            'Losing Trades': losing_trades,
            'Win Rate (%)': round(win_rate, 2),
            'Total P&L ($)': round(total_pnl, 2),
            'Average Win ($)': round(avg_win, 2),
            'Average Loss ($)': round(avg_loss, 2),
            'Profit Factor': round(profit_factor, 2) if profit_factor != float('inf') else 'N/A'
        }
        
        return summary
    
    def create_strategy_breakdown(self, df):
        """
        Create breakdown by strategy type
        """
        strategy_stats = df.groupby('Setup Type').agg({
            'P&L ($)': ['count', 'sum', 'mean'],
            'Win/Loss': lambda x: (x == 'Win').sum() / len(x) * 100
        }).round(2)
        
        strategy_stats.columns = ['Trades', 'Total P&L ($)', 'Avg P&L ($)', 'Win Rate (%)']
        
        return strategy_stats
    
    def export_to_excel(self, all_signals, filename=None):
        """
        Export all results to Excel with professional formatting
        """
        if filename:
            self.filename = filename
        
        # Create trades DataFrame
        trades_df = self.create_trades_dataframe(all_signals)
        
        # Create summary statistics
        summary_stats = self.create_summary_stats(trades_df)
        strategy_breakdown = self.create_strategy_breakdown(trades_df)
        
        # Create Excel writer
        with pd.ExcelWriter(self.filename, engine='openpyxl') as writer:
            # Write main trades data
            trades_df.to_excel(writer, sheet_name='Trades', index=False)
            
            # Write summary statistics
            summary_df = pd.DataFrame(list(summary_stats.items()), columns=['Metric', 'Value'])
            summary_df.to_excel(writer, sheet_name='Summary', index=False, startrow=0)
            
            # Write strategy breakdown
            strategy_breakdown.to_excel(writer, sheet_name='Summary', startrow=len(summary_df) + 3)
            
            # Write configuration parameters for easy modification
            config_data = []
            for strategy, params in Config.STRATEGIES.items():
                for param, value in params.items():
                    config_data.append({
                        'Strategy': strategy,
                        'Parameter': param,
                        'Value': value,
                        'Description': self.get_parameter_description(param)
                    })
            
            config_df = pd.DataFrame(config_data)
            config_df.to_excel(writer, sheet_name='Configuration', index=False)
        
        # Apply formatting
        self.format_excel_file()
        
        print(f"Results exported to: {self.filename}")
        return self.filename
    
    def get_parameter_description(self, param):
        """
        Get user-friendly descriptions for parameters
        """
        descriptions = {
            'enabled': 'Enable/disable this strategy',
            'min_gap_percent': 'Minimum gap percentage required',
            'target_retrace_percent': 'Target retrace percentage for profit',
            'max_float_millions': 'Maximum float in millions of shares',
            'min_volume_millions': 'Minimum volume in millions of shares',
            'min_green_days': 'Minimum consecutive green days required',
            'min_gap_down_percent': 'Minimum gap down percentage',
            'min_volume_ratio': 'Minimum volume vs average volume ratio',
            'breakout_period_days': 'Number of days for breakout analysis',
            'entry_time': 'Entry time for the strategy'
        }
        
        return descriptions.get(param, 'Strategy parameter')
    
    def format_excel_file(self):
        """
        Apply professional formatting to the Excel file
        """
        wb = openpyxl.load_workbook(self.filename)
        
        # Format Trades sheet
        if 'Trades' in wb.sheetnames:
            ws = wb['Trades']
            
            # Header formatting
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            
            for cell in ws[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center")
            
            # Auto-adjust column widths
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 20)
                ws.column_dimensions[column_letter].width = adjusted_width
            
            # Color code Win/Loss column
            win_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            loss_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            
            win_loss_col = None
            for idx, cell in enumerate(ws[1], 1):
                if cell.value == 'Win/Loss':
                    win_loss_col = idx
                    break
            
            if win_loss_col:
                for row in range(2, ws.max_row + 1):
                    cell = ws.cell(row=row, column=win_loss_col)
                    if cell.value == 'Win':
                        cell.fill = win_fill
                    elif cell.value == 'Loss':
                        cell.fill = loss_fill
        
        # Format Summary sheet
        if 'Summary' in wb.sheetnames:
            ws = wb['Summary']
            
            # Format summary statistics
            for row in range(1, ws.max_row + 1):
                for col in range(1, ws.max_column + 1):
                    cell = ws.cell(row=row, column=col)
                    if row == 1 or (cell.value and isinstance(cell.value, str) and 'Total' in str(cell.value)):
                        cell.font = Font(bold=True)
        
        wb.save(self.filename)
    
    def create_parameter_template(self):
        """
        Create an Excel template for easy parameter modification
        """
        template_filename = "strategy_parameters_template.xlsx"
        
        # Create a user-friendly parameter modification sheet
        param_data = []
        
        # Use DEFAULT_STRATEGIES to ensure we always get the hardcoded defaults,
        # not the potentially Excel-loaded values
        for strategy_name, params in Config.DEFAULT_STRATEGIES.items():
            param_data.append({
                'Strategy': strategy_name.replace('_', ' ').title(),
                'Parameter': 'Enabled',
                'Current Value': params.get('enabled', True),
                'Description': 'Turn this strategy on/off',
                'Recommended Range': 'True/False'
            })
            
            for param, value in params.items():
                if param != 'enabled':
                    param_data.append({
                        'Strategy': '',
                        'Parameter': param.replace('_', ' ').title(),
                        'Current Value': value,
                        'Description': self.get_parameter_description(param),
                        'Recommended Range': self.get_parameter_range(param)
                    })
        
        param_df = pd.DataFrame(param_data)
        
        with pd.ExcelWriter(template_filename, engine='openpyxl') as writer:
            param_df.to_excel(writer, sheet_name='Parameters', index=False)
            
            # Add instructions sheet
            instructions = pd.DataFrame({
                'Instructions': [
                    '🎯 HOW TO USE THIS FILE FOR BACKTESTING:',
                    '',
                    '1. Modify the "Current Value" column to change strategy parameters',
                    '2. Save this file',
                    '3. RESTART the program (python main.py)',
                    '4. Run backtest - the system will automatically use these parameters!',
                    '',
                    '📌 IMPORTANT NOTES:',
                    '• Parameters are loaded when the program STARTS',
                    '• Changes take effect AFTER restarting the program',
                    '• If this file exists, Excel parameters are used (NOT config.py)',
                    '• To use config.py instead, delete or rename this Excel file',
                    '',
                    '💡 PARAMETER TIPS:',
                    '• Higher gap percentages = more selective (fewer signals)',
                    '• Lower float = more volatile stocks',
                    '• Higher volume = more liquid stocks',
                    '• Test different combinations to optimize performance',
                    '',
                    '⚠️ IMPORTANT: Only modify the "Current Value" column!',
                    'Keep all other columns unchanged.',
                    '',
                    '📖 See PARAMETER_LOADING.md for complete documentation.'
                ]
            })
            instructions.to_excel(writer, sheet_name='Instructions', index=False)
        
        print(f"Parameter template created: {template_filename}")
        return template_filename
    
    def get_parameter_range(self, param):
        """
        Get recommended ranges for parameters
        """
        ranges = {
            'min_gap_percent': '50-150%',
            'target_retrace_percent': '30-70%',
            'max_float_millions': '10-500M',
            'min_volume_millions': '0.5-10M',
            'min_green_days': '10-30 days',
            'min_gap_down_percent': '3-20%',
            'min_volume_ratio': '1.5-5x',
            'breakout_period_days': '3-10 days'
        }
        
        return ranges.get(param, 'Varies')