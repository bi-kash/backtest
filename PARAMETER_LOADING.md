# Parameter Loading in Backtesting System

## Answer: Where does the system read parameters from?

**For actual backtesting, the system reads parameters in this priority order:**

1. **Excel file** (`strategy_parameters_template.xlsx`) - **IF IT EXISTS**
2. **config.py** - **IF Excel file doesn't exist**

## How It Works

### Automatic Loading on Startup

When you import any module (like `main.py`, `strategies.py`, or `backtest_engine.py`), the system automatically:

1. Checks if `strategy_parameters_template.xlsx` exists in the current directory
2. If Excel exists: Loads all parameters from the Excel file
3. If Excel doesn't exist: Uses the default values from `config.py`

### Visual Flow Chart

```
Start Program
     |
     v
Import config.py
     |
     v
Does strategy_parameters_template.xlsx exist?
     |
     +---> YES: Load parameters from Excel
     |          ✓ Excel parameters are used for backtesting
     |          
     +---> NO:  Use config.py defaults
                ✓ config.py parameters are used for backtesting
```

## For Non-Programmers: How to Modify Parameters

### Method 1: Excel (Recommended for Non-Programmers) ✨

1. **Create the template** (if it doesn't exist):
   ```bash
   python main.py
   # Choose option 5: Create Parameter Template
   ```

2. **Open the Excel file**: `strategy_parameters_template.xlsx`

3. **Modify values** in the "Current Value" column:
   - Change `min_gap_percent` from 70 to 100
   - Change `target_retrace_percent` from 50 to 30
   - Change `max_float_millions` from 50 to 20
   - etc.

4. **Save the Excel file**

5. **Run backtest** - the system will automatically use your Excel parameters!
   ```bash
   python main.py
   # Choose option 1: Run Full Backtest
   ```

### Method 2: config.py (For Programmers)

1. **Delete or rename** the Excel template:
   ```bash
   rm strategy_parameters_template.xlsx
   # or
   mv strategy_parameters_template.xlsx strategy_parameters_template.xlsx.backup
   ```

2. **Edit config.py** directly:
   ```python
   STRATEGIES = {
       'gap_up_short': {
           'enabled': True,
           'min_gap_percent': 100,  # Changed from 70
           'target_retrace_percent': 30,  # Changed from 50
           # ...
       }
   }
   ```

3. **Run backtest** - the system will use config.py parameters

## Important Notes

### Parameter Precedence

- **Excel ALWAYS wins** if it exists
- To use config.py parameters, you must **delete or rename** the Excel file
- The system prints which source it's using when it starts:
  ```
  ✓ Parameters loaded from Excel file: strategy_parameters_template.xlsx
  ```
  or
  ```
  Excel parameter file 'strategy_parameters_template.xlsx' not found. Using config.py defaults.
  ```

### When Parameters Are Loaded

Parameters are loaded **once** when the `config.py` module is first imported:
- This happens when you start `main.py`
- If you modify the Excel file, you need to **restart the program** to reload parameters
- Parameters are NOT reloaded between multiple backtests in the same session

### Best Practices

1. **For regular use**: Keep the Excel template and modify it as needed
2. **For version control**: Don't commit the Excel file (it may contain your custom parameters)
3. **For testing different parameters**: 
   - Save multiple Excel files (e.g., `strategy_params_aggressive.xlsx`, `strategy_params_conservative.xlsx`)
   - Rename the one you want to use to `strategy_parameters_template.xlsx`
4. **To reset to defaults**: Delete the Excel file and recreate it via option 5 in main menu

## Example Workflow

### Scenario: Testing Different Gap Percentages

```bash
# 1. Create initial template
python main.py  # Option 5

# 2. Modify Excel: set min_gap_percent to 50
# Save Excel file

# 3. Run backtest
python main.py  # Option 1
# Backtest uses min_gap_percent = 50

# 4. Modify Excel: change min_gap_percent to 100
# Save Excel file

# 5. Restart and run backtest again
python main.py  # Option 1
# Backtest uses min_gap_percent = 100
```

## Troubleshooting

### "My Excel changes aren't taking effect!"

**Solution**: Restart the program. Parameters are loaded once at startup.

### "How do I know which parameters are being used?"

**Solution**: Check the startup message:
- If it says "✓ Parameters loaded from Excel", your Excel values are used
- If it says "Using config.py defaults", config.py values are used

### "I want to temporarily use config.py parameters"

**Solution**: Rename the Excel file:
```bash
mv strategy_parameters_template.xlsx strategy_parameters_template.xlsx.backup
```

To restore:
```bash
mv strategy_parameters_template.xlsx.backup strategy_parameters_template.xlsx
```

## Technical Details (For Developers)

### Implementation

The parameter loading is implemented in `config.py`:

```python
class Config:
    # Default hardcoded values
    DEFAULT_STRATEGIES = { ... }
    
    # Active parameters (loaded from Excel or defaults)
    STRATEGIES = { ... }
    
    @staticmethod
    def load_parameters_from_excel(filename='strategy_parameters_template.xlsx'):
        # Load from Excel using openpyxl to preserve data types
        ...
    
    @staticmethod
    def initialize():
        # Called automatically when module is imported
        Config.load_parameters_from_excel()

# Auto-initialize on import
Config.initialize()
```

### Why Two Parameter Dictionaries?

- `DEFAULT_STRATEGIES`: Always contains hardcoded defaults from config.py
  - Used when creating Excel templates to ensure clean defaults
  - Never modified by Excel loading
  
- `STRATEGIES`: Contains active parameters used by strategies
  - Starts with same values as DEFAULT_STRATEGIES
  - Gets overwritten if Excel file exists
  - This is what strategies actually read from

### Data Type Handling

The system uses `openpyxl` directly (not pandas) to read Excel files because:
- Pandas converts integer 1 to boolean True (undesired)
- openpyxl preserves exact data types from Excel cells
- This ensures `min_volume_millions: 1` stays as integer 1, not boolean True

## Summary

**Quick Answer for "Where does it read parameters from for actual backtesting?"**

```
Excel file (strategy_parameters_template.xlsx)
                    ↓
        IF Excel exists: Use Excel values
        IF Excel doesn't exist: Use config.py defaults
                    ↓
            Strategies read from Config.STRATEGIES
                    ↓
                Backtesting runs
```

**To modify parameters for backtesting:**
1. Open `strategy_parameters_template.xlsx`
2. Change values in "Current Value" column
3. Save file
4. Restart program and run backtest
