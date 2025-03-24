# MoneyMageProto

A comprehensive personal finance management system for tracking, budgeting, and forecasting finances.

## Overview

MoneyMageProto is a Python-based personal finance toolkit designed to:
- Import and categorize transactions from multiple financial accounts
- Track spending against budgeted amounts
- Create projections and forecasts of future financial states
- Analyze spending patterns by category
- Support various budget types (monthly, quarterly, yearly, and loans)

## System Components

### Core Modules

1. **BudgetMeeting.py**: Main orchestration script that updates your budget with the latest transactions
   - Creates projections based on actual transactions and planned future spending
   - Generates ideal budgets and projections for future planning
   - Backs up budget files before making changes

2. **transactions.py**: Manages transaction data
   - Imports new transaction data from bank exports (Chase, Wells Fargo, Ally)
   - Automatically categorizes transactions based on description matching
   - Merges new transactions with existing transaction history
   - Detects and prevents duplicate transaction imports

3. **budget_functions.py**: Handles different budget types and calculations
   - Supports various budget types (loan, quarterly, monthly, yearly)
   - Calculates budget differences, reconciliations, and projections
   - Manages forward-looking budget plans based on actual spending

4. **excel_management.py**: Handles Excel file operations
   - Creates formatted Excel workbooks with multiple sheets
   - Applies appropriate formatting to different data types
   - Organizes budget categories in a logical order

5. **utilities.py**: Provides helper functions used throughout the system
   - Date handling and formatting
   - List processing and data cleaning
   - String similarity comparison for transaction matching

6. **get_sums.py**: Calculates summary totals for different time periods
   - Monthly, quarterly, and yearly summaries
   - Category-specific calculations

7. **parse_budget.py**: Parses budget data from Excel files
   - Extracts budget plans, reconciliations, and notes
   - Formats budget data for processing

8. **excel_diff_script.py**: Compares Excel files to identify changes
   - Useful for tracking changes between budget versions

### Budget Types

The system supports different budget types for various expense categories:

1. **Monthly**: Regular recurring expenses (groceries, utilities, etc.)
   - Tracked on a month-by-month basis
   - Shows monthly planned vs. actual spending

2. **Quarterly**: Expenses that occur quarterly (some subscriptions, etc.)
   - Divides annual budget into quarters
   - Tracks spending against quarterly allowances

3. **Yearly**: Annual expenses (insurance, memberships, etc.)
   - Sets an annual budget for the category
   - Tracks cumulative spending throughout the year

4. **Loan**: Fixed payments (mortgage, car loan, etc.)
   - Tracks regular payments against loans
   - Supports amortization calculations

## Setup

### Dependencies

This project requires:
- Python 3.8 or higher
- pandas
- openpyxl
- xlsxwriter
- numpy

### Virtual Environment Setup

It's recommended to use a virtual environment to manage dependencies:

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

See `VENV_SETUP.md` for more detailed instructions on setting up and using the virtual environment.

### Git Configuration

This project includes a `.gitignore` file configured to exclude:
- Excel files (*.xlsx, *.xls)
- Backup files in the archive/ directory
- Python cache files
- Virtual environment directories

To initialize the Git repository:

```bash
git init
git add .
git commit -m "Initial commit"
```

### Setting Up

1. Create initial Excel files:
   - `transactions.xlsx` - Stores all transaction history
   - `auto_categories.xlsx` - Maps transaction descriptions to categories
   - `Budget_YYYY.xlsx` - Main budget file with category sheets

2. Configure your financial accounts in the `get_new_transactions()` function in `transactions.py`

## Usage

### Running the System

1. Download transaction exports from your financial institutions
2. Activate your virtual environment
3. Run the budget meeting script:
   ```
   python BudgetMeeting.py -y 2025 -b Budget_2025.xlsx -t transactions.xlsx
   ```
   - `-y`: Budget year (default: 2025)
   - `-b`: Budget Excel filename (default: Budget_2025.xlsx)
   - `-t`: Transactions Excel filename (default: transactions.xlsx)

4. Review the updated budget file for:
   - Updated category sheets with actual vs. planned spending
   - Projection sheets showing future financial state
   - Summary sheets for quick review

### Budget File Structure

The budget Excel file contains multiple sheets:

1. **Category sheets**: One sheet per spending category with:
   - Transaction details (date, description, amount)
   - Reconciliation status
   - Monthly summaries (planned, actual, difference)
   - Future planned expenses

2. **Summary sheets**:
   - **Projection**: Forward-looking cash flow based on actual and planned transactions
   - **Monthly**: Monthly totals for each category
   - **Balances**: Account balance history and projections
   - **Expenses**: Yearly budget allowances by category
   - **Categories**: Defines the budget type for each category

## Maintenance

- Automated backups are created in the `archive/` directory before changes
- Review category assignments regularly in `auto_categories.xlsx`
- Update category types in the Categories sheet as needed

## Best Practices

1. **Regular Updates**: Import transactions weekly or monthly to keep projections accurate
2. **Categorization**: Maintain the auto-categorization rules to minimize manual categorization
3. **Yearly Planning**: Use the projection sheets to plan for the upcoming year
4. **Backup**: Keep copies of your budget files in case of data corruption

## Documentation

This project includes several documentation files:
- `README.md` - General overview and usage instructions
- `ARCHITECTURE.md` - Technical architecture and data flow
- `USAGE_GUIDE.md` - Detailed usage instructions and workflows
- `FINANCIAL_CONCEPTS.md` - Explanation of financial concepts
- `VENV_SETUP.md` - Virtual environment setup instructions