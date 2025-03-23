# MoneyMageProto Usage Guide

This guide provides step-by-step instructions for common tasks and workflows in the MoneyMageProto personal finance system.

## Initial Setup

### Creating Required Files

1. **transactions.xlsx**
   - Create a new Excel file named `transactions.xlsx`
   - Add sheets: "Transactions" and "Imported"
   - In "Transactions" sheet, add columns: Date, Amount, Category, Account, Description, R, Notes

2. **auto_categories.xlsx**
   - Create a new Excel file named `auto_categories.xlsx`
   - Add columns: Description, Category
   - Fill with common transaction descriptions and their corresponding categories
   - Example:
     ```
     Description              | Category
     ------------------------ | -------------
     WALMART                  | Groceries
     NETFLIX                  | Entertainment
     STATE FARM INSURANCE     | Insurance
     ```

3. **Budget_YYYY.xlsx** (where YYYY is the budget year)
   - Create a new Excel file named `Budget_YYYY.xlsx`
   - Add required sheets:
     - Categories (for category types)
     - Expenses (for yearly planned amounts)
     - Balances (for account balances)
     - One sheet per spending category

4. **Configure Account Paths**
   - Open `transactions.py`
   - Edit the `get_new_transactions()` function to set correct download paths for your system
   - Update the file patterns for your bank's export files

## Common Workflows

### 1. Monthly Budget Update

This workflow helps you update your budget with the latest transactions and review your financial position.

#### Step 1: Download Transaction Data
1. Log into your banking websites
2. Download transaction history as CSV files
3. Save files to your default downloads folder

#### Step 2: Run Budget Meeting
1. Open command prompt/terminal
2. Navigate to your MoneyMageProto directory
3. Run:
   ```
   python BudgetMeeting.py -y 2025 -b Budget_2025.xlsx -t transactions.xlsx
   ```
4. The script will:
   - Import new transactions
   - Categorize them automatically
   - Update your budget file with the new data
   - Create projections

#### Step 3: Review Results
1. Open the updated `Budget_YYYY.xlsx` file
2. Check the following sheets:
   - "Diffs" - Shows categories with budget discrepancies
   - "Q Summary" - Shows quarterly budget summary
   - "Projection" - Shows projected cash flow
   - Individual category sheets to see detailed spending

### 2. Adding a New Spending Category

This workflow helps you add a new spending category to your budget.

#### Step 1: Update Categories Sheet
1. Open `Budget_YYYY.xlsx`
2. Go to the "Categories" sheet
3. Add the new category name to the appropriate type column:
   - Monthly: for regular monthly expenses
   - Quarterly: for expenses that occur every quarter
   - Yearly: for annual expenses
   - Loan: for fixed payment loan expenses

#### Step 2: Add New Category Sheet
1. Create a new sheet named after your category
2. Add the following columns:
   - For Monthly/Quarterly/Yearly categories: Date, Desc., This Year, R, Next Year, Note
   - For Loan categories: Date, Desc., Payment, R, Next Year, Note

#### Step 3: Add to Expenses Sheet
1. Go to the "Expenses" sheet
2. Add a new row with your category name
3. Enter the yearly budget amount for this category

#### Step 4: Update auto_categories.xlsx
1. Open `auto_categories.xlsx`
2. Add entries that map common transaction descriptions to your new category

### 3. Year-End Budget Rollover

This workflow helps you set up a new budget year.

#### Step 1: Create New Budget File
1. Make a copy of your current `Budget_YYYY.xlsx` file
2. Rename it to `Budget_YYYY+1.xlsx` (e.g., Budget_2025.xlsx → Budget_2026.xlsx)

#### Step 2: Clear Transaction Data
1. For each category sheet:
   - Remove or mark as reconciled all transactions from the previous year
   - Update "Next Year" column values to the "This Year" column
   - Clear or update the "Next Year" column with new estimates

#### Step 3: Update Yearly Settings
1. Go to the "Expenses" sheet
2. Move "Next Year" values to "This Year" column
3. Enter new estimates in "Next Year" column

#### Step 4: Update Year Reference
1. Open `BudgetMeeting.py` in a text editor
2. Update the default year in the `if __name__ == '__main__'` section

#### Step 5: Run Initial Budget Meeting
1. Run the script to initialize your new budget:
   ```
   python BudgetMeeting.py -y 2026 -b Budget_2026.xlsx -t transactions.xlsx
   ```

### 4. Customizing Auto-Categorization

This workflow helps you improve automatic transaction categorization.

#### Step 1: Identify Missing Categories
1. Run a budget meeting
2. Look for transactions categorized as "uncategorized"
3. Note common transaction descriptions that weren't automatically categorized

#### Step 2: Update Auto-Categories
1. Open `auto_categories.xlsx`
2. Add new rows with:
   - Description: The transaction description (or a distinctive part of it)
   - Category: The correct category for this transaction

#### Step 3: Test Categorization
1. Run a budget meeting again
2. Verify that transactions are now correctly categorized
3. Fine-tune as needed

### 5. Creating Budget Reports and Analysis

This workflow helps you analyze your spending patterns.

#### Step 1: Review Monthly Sheet
1. Open your `Budget_YYYY.xlsx` file
2. Go to the "Monthly" sheet
3. Analyze category totals by month
4. Look for trends and outliers

#### Step 2: Check Category Detail
1. For categories with unusual spending:
   - Go to the individual category sheet
   - Review actual vs. planned spending
   - Check the "Difference" column

#### Step 3: Review Projections
1. Go to the "Projection" sheet
2. Review projected cash flow
3. Look for potential future issues
4. Compare with "Ideal Projection" sheet

## Troubleshooting

### Transaction Import Issues
- **Problem**: Transactions aren't importing
  - **Solution**: Check file paths in `get_new_transactions()` and ensure CSV files match expected patterns

- **Problem**: Duplicate transactions
  - **Solution**: The system should detect duplicates automatically. If issues persist, check the duplicate detection logic in `update_old_transactions()`

### Budget Calculation Issues
- **Problem**: Category totals don't match transactions
  - **Solution**: Check reconciliation status ('R' column) and ensure all transactions are correctly categorized

- **Problem**: Projection looks incorrect
  - **Solution**: Verify your account balances are correct in the "Balances" sheet

### Excel File Corruption
- **Problem**: Excel file won't open or is corrupted
  - **Solution**: Restore from a backup in the `archive/` folder
  - **Prevention**: Always let the script finish completely before opening Excel files

## Tips & Best Practices

1. **Consistent Categorization**: Use consistent categories for all transactions to ensure accurate reporting

2. **Regular Updates**: Import transactions weekly to keep your projections accurate

3. **Reconciliation**: Mark transactions as reconciled once verified to prevent them from being included in future projections

4. **Budget Planning**: Use the "Projection" sheet to identify potential cash flow issues months in advance

5. **Category Types**: Choose the appropriate category type based on expense frequency:
   - Monthly: Regular monthly expenses (groceries, utilities)
   - Quarterly: Expenses occurring every 3 months
   - Yearly: Annual expenses (insurance, memberships)
   - Loan: Fixed payment schedules (mortgage, car payment)

6. **Account Structure**: Consider using separate accounts for different purposes (e.g., bills, discretionary spending, savings) to simplify tracking 