import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, date, timedelta
import os

def setup_plotting_style():
    """Set up a consistent plotting style for all visualizations"""
    sns.set_theme(style="whitegrid")
    plt.rcParams['figure.figsize'] = (12, 6)
    plt.rcParams['font.size'] = 12
    plt.rcParams['axes.labelsize'] = 14
    plt.rcParams['axes.titlesize'] = 16
    plt.rcParams['xtick.labelsize'] = 12
    plt.rcParams['ytick.labelsize'] = 12
    plt.rcParams['legend.fontsize'] = 12
    plt.rcParams['figure.titlesize'] = 18
    
    # Create a directory for saving plots if it doesn't exist
    if not os.path.exists('plots'):
        os.makedirs('plots')

def load_transaction_data(file_path='transactions.xlsx'):
    """Load and prepare transaction data"""
    df = pd.read_excel(file_path)
    # Ensure Date is datetime
    if not pd.api.types.is_datetime64_any_dtype(df['Date']):
        df['Date'] = pd.to_datetime(df['Date'])
    return df

def load_budget_data(file_path='Budget_2025.xlsx'):
    """Load budget data from various sheets"""
    # Load different sheets
    monthly_budget = pd.read_excel(file_path, sheet_name='Monthly')
    projection = pd.read_excel(file_path, sheet_name='Projection')
    balances = pd.read_excel(file_path, sheet_name='Balances')
    
    # Prepare projection data
    if 'Date' in projection.columns and not pd.api.types.is_datetime64_any_dtype(projection['Date']):
        projection['Date'] = pd.to_datetime(projection['Date'])
    
    return {
        'monthly': monthly_budget,
        'projection': projection,
        'balances': balances
    }

def plot_monthly_spending_by_category(df, top_n=10, save=True):
    """Plot monthly spending by top N categories"""
    # Group by category and sum the amounts (negative values are expenses)
    category_spending = df[df['Amount'] < 0].groupby('Category')['Amount'].sum().abs()
    
    # Get the top N categories by spending
    top_categories = category_spending.nlargest(top_n)
    
    # Create the plot
    plt.figure(figsize=(12, 8))
    ax = sns.barplot(x=top_categories.values, y=top_categories.index, hue=top_categories.index, 
                    palette='viridis', legend=False)
    
    # Add labels and title
    plt.title(f'Top {top_n} Categories by Spending', fontweight='bold')
    plt.xlabel('Amount Spent ($)')
    plt.ylabel('Category')
    
    # Add value labels to bars
    for i, v in enumerate(top_categories.values):
        ax.text(v + 50, i, f'${v:.2f}', va='center')
    
    plt.tight_layout()
    
    if save:
        plt.savefig('plots/monthly_spending_by_category.png', dpi=300, bbox_inches='tight')
    
    plt.show()

def plot_spending_trend_over_time(df, top_categories=None, save=True):
    """Plot spending trend over time for selected categories"""
    # Ensure data is sorted by date
    df = df.sort_values('Date')
    
    # If no categories specified, use top 5 by total spending
    if top_categories is None:
        top_categories = df[df['Amount'] < 0].groupby('Category')['Amount'].sum().abs().nlargest(5).index.tolist()
    
    # Filter data to include only expenses in the specified categories
    filtered_df = df[(df['Amount'] < 0) & (df['Category'].isin(top_categories))]
    
    # Group by date and category, then sum amounts
    daily_spending = filtered_df.groupby(['Date', 'Category'])['Amount'].sum().abs().reset_index()
    
    # Create the plot
    plt.figure(figsize=(14, 8))
    
    # Plot each category as a line
    for category in top_categories:
        category_data = daily_spending[daily_spending['Category'] == category]
        if not category_data.empty:
            plt.plot(category_data['Date'], category_data['Amount'], marker='o', linewidth=2, label=category)
    
    # Add labels and title
    plt.title('Spending Trends Over Time by Category', fontweight='bold')
    plt.xlabel('Date')
    plt.ylabel('Amount Spent ($)')
    plt.legend(title='Category')
    plt.grid(True, alpha=0.3)
    
    # Format x-axis to show dates nicely
    plt.gcf().autofmt_xdate()
    
    plt.tight_layout()
    
    if save:
        plt.savefig('plots/spending_trend_over_time.png', dpi=300, bbox_inches='tight')
    
    plt.show()

def plot_income_vs_expenses(df, monthly=True, save=True):
    """Plot income vs expenses by month"""
    # Add a Month column if grouping by month
    if monthly:
        df = df.copy()
        df['Month'] = df['Date'].dt.strftime('%Y-%m')
        
        # Calculate income and expenses by month
        monthly_summary = df.groupby('Month').apply(
            lambda x: pd.Series({
                'Income': x[x['Amount'] > 0]['Amount'].sum(),
                'Expenses': abs(x[x['Amount'] < 0]['Amount'].sum()),
                'Net': x['Amount'].sum()
            })
        ).reset_index()
        
        # Sort by month
        monthly_summary['Month'] = pd.to_datetime(monthly_summary['Month'] + '-01')
        monthly_summary = monthly_summary.sort_values('Month')
        monthly_summary['Month'] = monthly_summary['Month'].dt.strftime('%Y-%m')
        
        # Create the plot
        plt.figure(figsize=(14, 8))
        
        x = range(len(monthly_summary))
        width = 0.35
        
        # Plot income and expenses as bars
        plt.bar([i - width/2 for i in x], monthly_summary['Income'], width, label='Income', color='green', alpha=0.7)
        plt.bar([i + width/2 for i in x], monthly_summary['Expenses'], width, label='Expenses', color='red', alpha=0.7)
        
        # Plot net as a line
        plt.plot(x, monthly_summary['Net'], marker='o', linestyle='-', color='blue', linewidth=2, label='Net')
        
        plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # Add labels and title
        plt.title('Monthly Income vs Expenses', fontweight='bold')
        plt.xlabel('Month')
        plt.ylabel('Amount ($)')
        plt.xticks(x, monthly_summary['Month'], rotation=45)
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        # Add value labels
        for i, v in enumerate(monthly_summary['Income']):
            plt.text(i - width/2, v + 100, f'${v:.0f}', ha='center', va='bottom', color='green', fontweight='bold')
        
        for i, v in enumerate(monthly_summary['Expenses']):
            plt.text(i + width/2, v + 100, f'${v:.0f}', ha='center', va='bottom', color='red', fontweight='bold')
        
        for i, v in enumerate(monthly_summary['Net']):
            plt.text(i, v + (100 if v >= 0 else -100), f'${v:.0f}', ha='center', va='bottom' if v >= 0 else 'top', 
                     color='blue', fontweight='bold')
        
        plt.tight_layout()
        
        if save:
            plt.savefig('plots/monthly_income_vs_expenses.png', dpi=300, bbox_inches='tight')
        
        plt.show()

def plot_balance_projection(budget_data, save=True):
    """Plot projected account balances over time"""
    projection = budget_data['projection']
    
    # Create the plot
    plt.figure(figsize=(14, 8))
    
    plt.plot(projection['Date'], projection['Balance'], marker='o', linewidth=2, color='blue')
    
    # Add labels and title
    plt.title('Projected Account Balance Over Time', fontweight='bold')
    plt.xlabel('Date')
    plt.ylabel('Balance ($)')
    plt.grid(True, alpha=0.3)
    
    # Format x-axis to show dates nicely
    plt.gcf().autofmt_xdate()
    
    # Add horizontal line at zero
    plt.axhline(y=0, color='red', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    
    if save:
        plt.savefig('plots/balance_projection.png', dpi=300, bbox_inches='tight')
    
    plt.show()

def plot_spending_by_account(df, save=True):
    """Plot spending by account"""
    # Group by account and sum the amounts (negative values are expenses)
    account_spending = df[df['Amount'] < 0].groupby('Account')['Amount'].sum().abs()
    
    # Create the plot - pie chart
    plt.figure(figsize=(10, 10))
    
    # Generate color palette
    colors = sns.color_palette('viridis', len(account_spending))
    
    plt.pie(account_spending.values, labels=account_spending.index, autopct='%1.1f%%', 
            startangle=90, colors=colors, shadow=False, wedgeprops={'edgecolor': 'w'})
    
    # Add title
    plt.title('Spending Distribution by Account', fontweight='bold')
    
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    
    if save:
        plt.savefig('plots/spending_by_account.png', dpi=300, bbox_inches='tight')
    
    plt.show()
    
    # Also create a bar chart for the same data
    plt.figure(figsize=(12, 8))
    ax = sns.barplot(x=account_spending.index, y=account_spending.values, hue=account_spending.index, 
                    palette='viridis', legend=False)
    
    # Add labels and title
    plt.title('Spending by Account', fontweight='bold')
    plt.xlabel('Account')
    plt.ylabel('Amount Spent ($)')
    
    # Add value labels to bars
    for i, v in enumerate(account_spending.values):
        ax.text(i, v + 50, f'${v:.2f}', ha='center', va='bottom')
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    if save:
        plt.savefig('plots/spending_by_account_bar.png', dpi=300, bbox_inches='tight')
    
    plt.show()

def plot_monthly_budget_vs_actual(budget_data, transactions_df, category, save=True):
    """Plot monthly budget vs actual spending for a specific category"""
    monthly = budget_data['monthly']
    
    # Get the row for the specified category
    category_row = monthly[monthly['Categories'] == category]
    
    if category_row.empty:
        print(f"Category '{category}' not found in monthly budget data")
        return
    
    # Get the monthly budgeted amounts, excluding the Categories and Yearly columns
    months = [col for col in monthly.columns if col not in ['Categories', 'Yearly']]
    budgeted_amounts = category_row[months].values[0]
    
    # Convert month names to datetime for sorting
    month_dates = pd.to_datetime([m.split(' ')[0] + ' 1, ' + m.split(' ')[1] for m in months])
    sorted_indices = month_dates.argsort()
    sorted_months = [months[i] for i in sorted_indices]
    sorted_budgeted = [budgeted_amounts[i] for i in sorted_indices]
    
    # Get actual spending for each month
    transactions_df = transactions_df.copy()
    transactions_df['Month'] = transactions_df['Date'].dt.strftime('%B %Y')
    
    actual_spending = []
    for month in sorted_months:
        # Get transactions for this category and month
        month_transactions = transactions_df[(transactions_df['Category'] == category) & 
                                           (transactions_df['Month'] == month)]
        # Sum the amounts and convert to positive for expenses
        if month_transactions.empty:
            actual_spending.append(0)
        else:
            month_total = month_transactions['Amount'].sum()
            # If the budget is negative (expense), convert actual to positive for comparison
            if category_row[month].values[0] < 0:
                actual_spending.append(abs(month_total))
            else:
                actual_spending.append(month_total)
    
    # Create the plot
    plt.figure(figsize=(14, 8))
    
    x = range(len(sorted_months))
    width = 0.35
    
    # Plot budgeted and actual as bars
    # Convert budgeted amounts to absolute values for expenses (negative values)
    plot_budgeted = [abs(b) if b < 0 else b for b in sorted_budgeted]
    
    plt.bar([i - width/2 for i in x], plot_budgeted, width, label='Budgeted', color='blue', alpha=0.7)
    plt.bar([i + width/2 for i in x], actual_spending, width, label='Actual', color='green', alpha=0.7)
    
    # Add labels and title
    plt.title(f'Monthly Budget vs Actual: {category}', fontweight='bold')
    plt.xlabel('Month')
    plt.ylabel('Amount ($)')
    plt.xticks([i for i in x], [m.split(' ')[0] for m in sorted_months], rotation=45)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Add value labels
    for i, v in enumerate(plot_budgeted):
        if v > 0:  # Only add labels for non-zero values
            plt.text(i - width/2, v + max(plot_budgeted + actual_spending) * 0.02, f'${v:.0f}', 
                     ha='center', va='bottom', color='blue', fontweight='bold')
    
    for i, v in enumerate(actual_spending):
        if v > 0:  # Only add labels for non-zero values
            plt.text(i + width/2, v + max(plot_budgeted + actual_spending) * 0.02, f'${v:.0f}', 
                     ha='center', va='bottom', color='green', fontweight='bold')
    
    plt.tight_layout()
    
    if save:
        plt.savefig(f'plots/monthly_budget_vs_actual_{category.replace(" ", "_")}.png', dpi=300, bbox_inches='tight')
    
    plt.show()

def generate_all_plots():
    """Generate all plots"""
    # Set up plotting style
    setup_plotting_style()
    
    # Load data
    transactions_df = load_transaction_data()
    budget_data = load_budget_data()
    
    # Generate plots
    plot_monthly_spending_by_category(transactions_df)
    
    # Plot spending trends for top 5 categories
    top_spending_categories = transactions_df[transactions_df['Amount'] < 0].groupby('Category')['Amount'].sum().abs().nlargest(5).index.tolist()
    plot_spending_trend_over_time(transactions_df, top_categories=top_spending_categories)
    
    # Plot income vs expenses
    plot_income_vs_expenses(transactions_df)
    
    # Plot balance projection
    plot_balance_projection(budget_data)
    
    # Plot spending by account
    plot_spending_by_account(transactions_df)
    
    # Plot budget vs actual for some important categories
    important_categories = ['Groceries', 'Restaurant', 'Mortgage', 'Auto - Gas', 'Home Supplies']
    for category in important_categories:
        plot_monthly_budget_vs_actual(budget_data, transactions_df, category)

if __name__ == "__main__":
    generate_all_plots() 