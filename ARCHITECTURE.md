# MoneyMageProto System Architecture

This document illustrates the architecture and data flow of the MoneyMageProto personal finance system.

## System Flow Diagram

```
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│                     │   │                     │   │                     │
│  Bank Transactions  │   │  auto_categories.   │   │  Budget_YYYY.xlsx   │
│  CSV Exports        │   │  xlsx               │   │  (Starting Budget)  │
│                     │   │                     │   │                     │
└───────────┬─────────┘   └─────────┬───────────┘   └──────────┬──────────┘
            │                       │                          │
            ▼                       │                          │
┌───────────────────────┐           │                          │
│                       │           │                          │
│  transactions.py      │◄──────────┘                          │
│  - Import transactions│                                      │
│  - Auto-categorize    │                                      │
│  - Detect duplicates  │                                      │
│                       │                                      │
└───────────┬───────────┘                                      │
            │                                                  │
            ▼                                                  │
┌───────────────────────┐                                      │
│                       │                                      │
│  transactions.xlsx    │                                      │
│  - Stored transaction │                                      │
│    history            │                                      │
│                       │                                      │
└───────────┬───────────┘                                      │
            │                                                  │
            │           ┌────────────────────────────────┐     │
            └──────────►│                                │◄────┘
                        │  BudgetMeeting.py              │
                        │  - Main orchestration script   │
                        │  - Updates budget with         │
                        │    transactions                │
                        │  - Creates projections         │
                        │                                │
                        └───────────┬────────────────────┘
                                    │
                                    │    ┌────────────────────────┐
                                    │    │                        │
                                    │    │  utilities.py          │
                                    │    │  - Helper functions    │
                                    │    │                        │
                                    │    └────────────────────────┘
                                    │             ▲
                                    │             │
                                    ▼             │
          ┌─────────────────────────────────────────────────────────┐
          │                                                         │
          │  Core Processing Modules                                │
          │  ┌─────────────────────┐  ┌─────────────────────┐      │
          │  │                     │  │                     │      │
          │  │  parse_budget.py    │  │  budget_functions.py│      │
          │  │  - Parse budget data│  │  - Budget type logic│      │
          │  │                     │  │                     │      │
          │  └─────────┬───────────┘  └─────────┬───────────┘      │
          │            │                        │                  │
          │            │  ┌─────────────────────┐                  │
          │            │  │                     │                  │
          │            └─►│  get_sums.py        │◄─────────────────┘
          │               │  - Calculate summary│
          │               │    totals          │
          │               │                     │
          │               └─────────┬───────────┘
          │                         │
          └─────────────────────────┘
                                    │
                                    ▼
                       ┌─────────────────────────┐
                       │                         │
                       │  excel_management.py    │
                       │  - Format and write     │
                       │    Excel output         │
                       │                         │
                       └─────────────┬───────────┘
                                     │
                                     ▼
                       ┌─────────────────────────┐
                       │                         │
                       │  Updated Budget_YYYY.xlsx│
                       │  - Category sheets      │
                       │  - Projections          │
                       │  - Summary sheets       │
                       │                         │
                       └─────────────────────────┘
```

## Data Flow

1. **Transaction Import**:
   - Bank transaction CSV files are downloaded from financial institutions
   - `transactions.py` processes these files and merges with existing transaction history
   - Transactions are auto-categorized using rules from `auto_categories.xlsx`
   - Processed transactions are stored in `transactions.xlsx`

2. **Budget Meeting Process**:
   - `BudgetMeeting.py` orchestrates the budget update process
   - Imports transactions from `transactions.xlsx`
   - Reads the current budget state from `Budget_YYYY.xlsx`
   - Creates a backup of the current budget file

3. **Budget Processing**:
   - `parse_budget.py` extracts budget data from Excel sheets
   - `budget_functions.py` processes each category according to its type (monthly, quarterly, yearly, loan)
   - `get_sums.py` calculates totals for different time periods
   - `utilities.py` provides helper functions for data processing

4. **Output Generation**:
   - `excel_management.py` writes the updated budget to Excel
   - Creates formatted sheets for each category
   - Generates projection and summary sheets
   - Outputs the updated `Budget_YYYY.xlsx` file

## Data Structures

1. **Transaction Data**:
   - Date: Transaction date
   - Amount: Transaction amount (positive for income, negative for expenses)
   - Category: Spending/income category
   - Description: Transaction description from bank
   - Account: Source account
   - R: Reconciliation flag
   - Notes: Additional information

2. **Budget Categories**:
   - Monthly: Regular recurring expenses
   - Quarterly: Expenses divided into quarters
   - Yearly: Annual expenses with yearly caps
   - Loan: Fixed payment schedules

3. **Budget Sheets**:
   - Category sheets: Detailed transactions and plans
   - Projection: Forward-looking cash flow
   - Monthly: Monthly summaries by category
   - Expenses: Yearly budget allocations
   - Categories: Category type definitions

## Key Algorithm Concepts

1. **Auto-categorization**:
   - Uses string similarity matching to automatically categorize transactions
   - Threshold-based matching (>0.7 similarity) against known descriptions

2. **Reconciliation**:
   - Transactions are marked as reconciled ('R' column)
   - Reconciled transactions are excluded from future projections

3. **Projections**:
   - Combines actual spending with planned future expenses
   - Creates multi-year forecasts based on current patterns
   - Generates "ideal" budget projections for comparison

4. **Budget Tracking**:
   - Tracks actual vs. planned spending for each category
   - Calculates remaining budget for each category
   - Identifies out-of-balance categories 