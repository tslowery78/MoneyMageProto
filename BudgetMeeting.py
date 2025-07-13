import argparse
import datetime
import os
import pandas as pd
from utilities import remove_empty_rows
from parse_budget import parse_budget
from excel_management import write_budget
from transactions import get_transactions, update_auto_categories
from budget_functions import remove_budget_integers, get_forward_budget
from get_sums import get_monthly_sums
from pandas.errors import ParserError
import shutil


def update_budget(budget_xlsx, transactions, this_year):
    """Function to update the budget with the latest transactions"""

    
    # Read in the budget xlsx
    os.makedirs('archive/', exist_ok=True)
    back_up_xls = budget_xlsx.split('.')[0] \
                  + f'_{datetime.date.today().month}_{datetime.date.today().day}_{datetime.date.today().year}_' \
                    f'{datetime.datetime.today().second}.xlsx'
    shutil.copy(f'{budget_xlsx}', f'archive/{back_up_xls}')

    b = pd.ExcelFile(budget_xlsx, engine='openpyxl')

    # Read the category types
    df_categories = b.parse(sheet_name='Categories').fillna('')
    category_types = df_categories.to_dict('list')

    # Read in the yearly planned expenses
    df_expenses = b.parse(sheet_name='Expenses')
    expenses = df_expenses.to_dict('list')

    # Get the categories that are represented in the transactions list
    if transactions:
        categories = list(set(transactions['Category'] + b.sheet_names))
    else:
        categories = b.sheet_names

    # Parse the budget
    excluded = ['Projection', 'Monthly', 'Expenses', 'Savings', 'Balances', 'Credit Card', 'Categories',
                'Ideal Monthly', 'Ideal Projection', 'Projection Balances', 'Diffs', 'Q Summary', 'Y Summary', 'Yearly Remaining']
    budgets = {}
    projections = {}
    forecasts = {}
    projection_list = [[], [], [], [], [], []]
    next_year_budget_list = [[], [], [], [], [], []]
    missing_budgets = []
    for category in categories:
        if category in excluded:
            continue
        if category in b.sheet_names:
            try:
                df_budget = b.parse(sheet_name=category, usecols="A:F").fillna('')
            except ParserError:
                df_budget = b.parse(sheet_name=category).fillna('')

            if df_budget.columns.empty:
                budget = {'Date': [], 'Desc.': [], 'This Year': [], 'R': [], 'Next Year': [], 'Note': []}
            else:
                df_budget[df_budget.columns[0]] = df_budget[df_budget.columns[0]].fillna('')
                budget = df_budget.to_dict('list')

            if 'Date' in budget.keys():
                budget['Date'] = ['' if pd.isna(x) else x for x in budget['Date']]
                budget = remove_empty_rows(budget, 'Date')
                budget['Date'] = [datetime.datetime.strptime(x.split(',')[0], '%m/%d/%Y').date()
                                  if isinstance(x, str) else x.date() for x in budget['Date']]
            budget = remove_budget_integers(budget)
            budgets[category], projections[category], forecasts[category] = \
                parse_budget(category, budget, transactions, expenses, category_types, this_year)

            # Create the projection sheet
            for i in range(0, 6):
                projection_list[i].extend([x[i] for x in projections[category]])
                next_year_budget_list[i].extend([x[i] for x in forecasts[category][0]])
                for forecast_year_list in forecasts[category]:
                    projection_list[i].extend([x[i] for x in forecast_year_list])
        else:
            budget = {'Date': [], 'Desc.': [], 'This Year': [], 'R': [], 'Next Year': [], 'Note': []}
            budgets[category], projections[category], forecasts[category] = \
                parse_budget(category, budget, transactions, expenses, category_types, this_year)
            # Determine category monthly totals for all transactions
            missing_budgets.append(category)
            category_monthly_sums = get_monthly_sums(category, transactions['Date'],
                                                     transactions['Amount'], transactions['Category'])
            category_monthly_sums = [x for x in category_monthly_sums if abs(x[1]) > 0.0]
            monthly_transactions = [[x[0], f'{category} transactions for {x[0].strftime("%B")} {x[0].year}',
                                     x[1], category, 0.0, ''] for i, x in enumerate(category_monthly_sums)]
            for i in range(0, 6):
                projection_list[i].extend([x[i] for x in monthly_transactions])
            pass

    # Determine category summaries and out of balance categories
    differences = {}
    quarterly_months = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]
    i_month = datetime.datetime.today().month
    
    q_summary_data = {1: [], 2: [], 3: [], 4: []}
    
    yearly_summary = {'Category': [], 'Planned': [], 'Spent': [], 'Remaining': []}
    for category in categories:
        if category in excluded:
            continue
        if category in category_types['Loan']:
            differences[category] = sum([x for x in budgets[category]['Difference'] if isinstance(x, float)])
        elif category in category_types['Yearly']:
            differences[category] = sum([x for x in budgets[category]['Difference'] if isinstance(x, float)])
            yearly_summary['Category'].append(category)
            yearly_summary['Planned'].append(sum([x for x in budgets[category].get('This Year', []) if isinstance(x, (int, float))]))
            yearly_summary['Spent'].append(sum([x for x in budgets[category].get('Actual', []) if isinstance(x, (int, float))]))
            yearly_summary['Remaining'].append(sum([x for x in budgets[category].get('Remaining', []) if isinstance(x, (int, float))]))
        elif category in category_types['Quarterly']:
            for i in range(4):
                q_summary_data[i+1].append({
                    'Category': category,
                    'Planned': budgets[category]['This Year'][i],
                    'Spent': budgets[category]['Spent'][i],
                    'Remaining': budgets[category]['Remaining'][i]
                })
        elif category in category_types['Monthly']:
            for i in range(4):
                q_months = quarterly_months[i]
                
                planned = sum(budgets[category]['Planned'][m-1] for m in q_months)
                spent = sum(budgets[category]['Spent'][m-1] for m in q_months)
                remaining = sum(budgets[category]['Remaining'][m-1] for m in q_months)
                
                q_summary_data[i+1].append({
                    'Category': category,
                    'Planned': planned,
                    'Spent': spent,
                    'Remaining': remaining
                })
        else:
            differences[category] = sum([x for x in budgets[category]['Difference'] if isinstance(x, float)])
    diff_outs = {}
    for k,v in differences.items():
        if abs(v) > 0.01:
            diff_outs[k] = v

    # Write out the missing budgets
    print(f'These categories were found in the transactions, and do not have a budget sheet in {budget_xlsx}:')
    for missing_budget in missing_budgets:
        print(f'  {missing_budget}')

    # Read the balances sheet
    df_balances = b.parse(sheet_name='Balances')
    # Clean out non-numeric values and get the last valid balance
    valid_balances = pd.to_numeric(df_balances['Balance'], errors='coerce').dropna()
    if not valid_balances.empty:
        balance = valid_balances.iloc[-1]
    else:
        balance = 0.0
    balances_dict = df_balances.to_dict('list')

    # Set the initial sheets
    initial_sheets = {'Balances': balances_dict, 'Expenses': expenses, 'Categories': category_types}

    # Find projection dict
    # this_year = datetime.date.today().year
    projection_dict, monthly_sums_dict = make_projection_dict(projection_list, balance, this_year)

    # Find ideal budget
    ideal_budget, ideal_monthly_budget = find_ideal(projection_list)
    ideal_dict, ideal_monthly_sums_dict = make_projection_dict(ideal_budget, 0.0, this_year + 1)

    # Calculate remaining expenses for the year
    remaining_expenses = calculate_remaining_expenses_from_sheets(budget_xlsx, category_types, this_year)

    # Write out the updated budget
    b.close()
    write_budget(budgets, projection_dict, initial_sheets, monthly_sums_dict, budget_xlsx, category_types,
                 ideal_dict, ideal_monthly_sums_dict, diff_outs, q_summary_data, yearly_summary, remaining_expenses, this_year)

    pass


def calculate_remaining_expenses_from_sheets(budget_xlsx, category_types, this_year):
    """Function to calculate the remaining expenses for each category for the next 5 years.
    
    Reads directly from the budget sheets to get future year data:
    - Looks at Date/Payment columns for future year expenses
    - Uses category types to determine appropriate logic for each category
    """
    years = [this_year + i for i in range(5)]  # 5 years total
    
    remaining_by_category = {'Category': []}
    for year in years:
        remaining_by_category[str(year)] = []
    
    # Read the budget file
    b = pd.ExcelFile(budget_xlsx, engine='openpyxl')
    
    # Get all sheet names except excluded ones
    excluded = ['Projection', 'Monthly', 'Expenses', 'Savings', 'Balances', 'Credit Card', 'Categories',
                'Ideal Monthly', 'Ideal Projection', 'Projection Balances', 'Diffs', 'Q Summary', 'Y Summary', 'Yearly Remaining']
    
    all_categories = [sheet for sheet in b.sheet_names if sheet not in excluded]
    all_categories.sort()
    
    for category in all_categories:
        remaining_by_category['Category'].append(category)
        
        # Read the category sheet
        try:
            df_category = pd.read_excel(budget_xlsx, sheet_name=category)
        except:
            # If we can't read the sheet, fill with zeros
            for year in years:
                remaining_by_category[str(year)].append(0.0)
            continue
        
        # Determine category type
        is_yearly = category in category_types.get('Yearly', [])
        is_monthly = category in category_types.get('Monthly', [])
        is_quarterly = category in category_types.get('Quarterly', [])
        is_loan = category in category_types.get('Loan', [])
        
        for year in years:
            remaining_amount = 0.0
            
            if year == this_year:
                # Current year: multiple approaches to find remaining amounts
                
                # 1st Priority: Use 'Remaining' column if available
                if 'Remaining' in df_category.columns:
                    remaining_values = df_category['Remaining'].dropna()
                    remaining_amount = sum([x for x in remaining_values if isinstance(x, (int, float))])
                
                # 2nd Priority: Calculate from current year entries only
                elif 'Date' in df_category.columns:
                    df_category['Date'] = pd.to_datetime(df_category['Date'], errors='coerce')
                    current_year_mask = df_category['Date'].dt.year == year
                    
                    # Look for amount in Payment column first, then This Year column
                    amount_column = None
                    if 'Payment' in df_category.columns:
                        amount_column = 'Payment'
                    elif 'This Year' in df_category.columns:
                        amount_column = 'This Year'
                    
                    if amount_column:
                        current_year_payments = df_category[current_year_mask][amount_column].dropna()
                        remaining_amount = sum([x for x in current_year_payments if isinstance(x, (int, float))])
                
                # 3rd Priority: Use 'This Year' column as fallback (only if no Date column)
                elif 'This Year' in df_category.columns:
                    this_year_values = df_category['This Year'].dropna()
                    remaining_amount = sum([x for x in this_year_values if isinstance(x, (int, float))])
                
            else:
                # Future years: Combine baseline + specific year expenses
                
                # Start with baseline from "Next Year" column (regular annual expenses)
                baseline_amount = 0.0
                if 'Next Year' in df_category.columns:
                    next_year_values = df_category['Next Year'].dropna()
                    baseline_amount = sum([x for x in next_year_values if isinstance(x, (int, float))])
                
                # Add any specific expenses for this year (major repairs, purchases, etc.)
                specific_year_amount = 0.0
                if 'Date' in df_category.columns:
                    # Convert Date column to datetime
                    df_category['Date'] = pd.to_datetime(df_category['Date'], errors='coerce')
                    
                    # Get payments for this specific year from appropriate amount column
                    year_mask = df_category['Date'].dt.year == year
                    
                    # Look for amount in Payment column first, then This Year column
                    amount_column = None
                    if 'Payment' in df_category.columns:
                        amount_column = 'Payment'
                    elif 'This Year' in df_category.columns:
                        amount_column = 'This Year'
                    
                    if amount_column:
                        year_payments = df_category[year_mask][amount_column].dropna()
                        specific_year_amount = sum([x for x in year_payments if isinstance(x, (int, float))])
                
                # Combine baseline + specific year expenses
                if baseline_amount != 0 or specific_year_amount != 0:
                    remaining_amount = baseline_amount + specific_year_amount
                else:
                    # Fallback to planning logic based on category type
                    if is_monthly and 'Planned' in df_category.columns:
                        # Monthly: use planned amounts
                        planned_values = df_category['Planned'].dropna()
                        remaining_amount = sum([x for x in planned_values if isinstance(x, (int, float))])
                    elif is_quarterly and 'This Year' in df_category.columns:
                        # Quarterly: use this year as template
                        quarterly_values = df_category['This Year'].dropna()
                        remaining_amount = sum([x for x in quarterly_values if isinstance(x, (int, float))])
            
            remaining_by_category[str(year)].append(remaining_amount)
    
    b.close()
    return remaining_by_category




def find_monthly_sums(projection_list, year):
    """Function to find the monthly sums for a projection list"""

    monthly_sums_dict = {}
    projection_categories = list(set([x[3] for x in projection_list]))
    for category in projection_categories:
        category_projection_list = [x for x in projection_list if x[3] == category
                                    and x[0] < datetime.date(year + 1, 1, 1)]
        monthly_sums_dict[category] = get_monthly_sums(None, [x[0] for x in category_projection_list],
                                                       [x[2] for x in category_projection_list], None)

    return monthly_sums_dict


def find_ideal(projection_list):
    """Function to find the ideal budget for a year"""

    this_year = datetime.date.today().year
    start_date = datetime.date(this_year + 1, 1, 1)
    end_date = datetime.date(this_year + 1, 12, 31)

    i_ideal_budget = [i for i, x in enumerate(projection_list[0])
                    if start_date <= x <= end_date and 'Forecast:' in projection_list[1][i]]
    ideal_budget = [[x[i] for i in i_ideal_budget] for x in projection_list]
    ideal_monthly_budget = get_monthly_sums(None, [x for x in ideal_budget[0]], [x for x in ideal_budget[2]], None)

    return ideal_budget, ideal_monthly_budget


def make_projection_dict(projection_list, balance, year):
    """Function to make the projection dict"""

    # Sort projection by Date
    projection_tuples = list(zip(projection_list[0], projection_list[1], projection_list[2],
                                 projection_list[3], projection_list[4], projection_list[5]))
    projection_tuples.sort()
    projection_list = [list(x) for x in projection_tuples]

    # Fill in the balance column
    current_balance = balance
    for i, transaction_tuple in enumerate(projection_list):
        current_balance += transaction_tuple[2]
        projection_list[i][4] = current_balance

    # Get the monthly sums for each category
    monthly_sums_dict = find_monthly_sums(projection_list, year)

    # Create projection dict for xls output
    projection_dict = {'Date': [], 'Desc.': [], 'Amount': [], 'Category': [], 'Balance': [], 'Note': []}
    projection_columns = ['Date', 'Desc.', 'Amount', 'Category', 'Balance', 'Note']
    for i, projection_column in enumerate(projection_columns):
        projection_dict[projection_column] = [x[i] for x in projection_list]

    return projection_dict, monthly_sums_dict


def BudgetMeeting(budget_xlsx, transactions_xlsx, this_year):
    """Make a budget"""

    print(f"Processing budget file: {budget_xlsx}")
    print(f"Processing transactions file: {transactions_xlsx}")

    # Get the latest transactions
    transactions = get_transactions(transactions_xlsx)
    
    if transactions:
        print(f"Found {len(transactions['Date'])} new transactions.")
    else:
        print("No new transactions found.")

    # Update the budget with the latest transactions
    update_budget(budget_xlsx, transactions, this_year)

    # Update auto categories
    print("Updating auto-categorization rules...")
    update_auto_categories(transactions_xlsx=transactions_xlsx)
    
    print("Budget update complete.")


if __name__ == '__main__':

    # Get args
    parser = argparse.ArgumentParser()
    parser.add_argument('-y', help='the year of the budget', type=int, default=2025)
    parser.add_argument('-b', help='budget xls', default='Budget_2025.xlsx')
    parser.add_argument('-t', help='trans xls', default='transactions.xlsx')
    args = parser.parse_args()

    # Do the budget
    BudgetMeeting(args.b, args.t, args.y)

