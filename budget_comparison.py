import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from datetime import datetime
import glob
from visualization import setup_plotting_style, load_budget_data, load_transaction_data

def get_budget_versions(date_pattern=None):
    """Find budget file versions based on a date pattern
    
    Args:
        date_pattern: Date pattern to match (e.g., '3_23_2025')
        
    Returns:
        List of budget filenames sorted by timestamp
    """
    if date_pattern:
        pattern = f"archive/Budget_2025_{date_pattern}_*.xlsx"
    else:
        pattern = "archive/Budget_2025_*.xlsx"
    
    budget_files = glob.glob(pattern)
    
    # Sort by timestamp in filename
    budget_files.sort(key=lambda x: x.split('_')[-1].split('.')[0])
    
    return budget_files

def get_transaction_versions(date_pattern=None):
    """Find transaction file versions based on a date pattern
    
    Args:
        date_pattern: Date pattern to match (e.g., '3_23_2025')
        
    Returns:
        List of transaction filenames sorted by timestamp
    """
    if date_pattern:
        pattern = f"archive/transactions_{date_pattern}_*.xlsx"
    else:
        pattern = "archive/transactions_*.xlsx"
    
    transaction_files = glob.glob(pattern)
    
    # Sort by timestamp in filename
    transaction_files.sort(key=lambda x: x.split('_')[-1].split('.')[0])
    
    return transaction_files

def load_budget_versions(current_file, previous_file=None):
    """Load current and previous budget versions
    
    Args:
        current_file: Path to current budget file
        previous_file: Path to previous budget file (if None, will use oldest file with same date pattern)
        
    Returns:
        Tuple of (current_data, previous_data)
    """
    current_data = load_budget_data(current_file)
    
    if previous_file is None:
        # Extract date pattern from current file and find previous version
        if '_' in current_file:
            parts = current_file.split('_')
            if len(parts) >= 4:
                date_pattern = '_'.join(parts[2:-1])
                budget_files = get_budget_versions(date_pattern)
                if len(budget_files) > 1 and budget_files[-1] == current_file:
                    previous_file = budget_files[0]  # Get earliest version
    
    if previous_file and os.path.exists(previous_file):
        previous_data = load_budget_data(previous_file)
    else:
        previous_data = None
    
    return current_data, previous_data, current_file, previous_file

def compare_monthly_budgets(current_data, previous_data):
    """Compare monthly budgets between two versions
    
    Args:
        current_data: Current budget data dictionary
        previous_data: Previous budget data dictionary
        
    Returns:
        DataFrame with differences
    """
    if previous_data is None:
        return None
    
    current_monthly = current_data['monthly']
    previous_monthly = previous_data['monthly']
    
    # Ensure they have the same structure
    if set(current_monthly.columns) != set(previous_monthly.columns):
        return None
    
    # Merge on Categories column
    merged = pd.merge(current_monthly, previous_monthly, on='Categories', suffixes=('_current', '_previous'))
    
    # Calculate differences for all numeric columns (exclude Categories)
    diff_df = pd.DataFrame()
    diff_df['Categories'] = merged['Categories']
    
    month_cols = [col for col in current_monthly.columns if col != 'Categories' and col != 'Yearly']
    
    for col in month_cols:
        diff_df[col] = merged[f'{col}_current'] - merged[f'{col}_previous']
    
    # Add yearly difference
    if 'Yearly' in current_monthly.columns and 'Yearly' in previous_monthly.columns:
        diff_df['Yearly'] = merged['Yearly_current'] - merged['Yearly_previous']
    
    return diff_df

def compare_balances(current_data, previous_data):
    """Compare account balances between two versions
    
    Args:
        current_data: Current budget data dictionary
        previous_data: Previous budget data dictionary
        
    Returns:
        DataFrame with differences
    """
    if previous_data is None:
        return None
    
    current_balances = current_data['balances']
    previous_balances = previous_data['balances']
    
    # Merge on Bank column
    merged = pd.merge(current_balances, previous_balances, on='Bank', suffixes=('_current', '_previous'))
    
    # Calculate differences
    diff_df = pd.DataFrame()
    diff_df['Bank'] = merged['Bank']
    diff_df['Current Balance'] = merged['Balance_current']
    diff_df['Previous Balance'] = merged['Balance_previous']
    diff_df['Difference'] = merged['Balance_current'] - merged['Balance_previous']
    diff_df['Percent Change'] = (diff_df['Difference'] / diff_df['Previous Balance'].abs()) * 100
    
    return diff_df

def plot_monthly_budget_changes(monthly_diff, top_n=10, save=True):
    """
    Plot changes in monthly budgets.
    
    Args:
        monthly_diff (DataFrame): DataFrame containing budget differences
        top_n (int): Number of top categories to show
        save (bool): Whether to save the plot
    """
    if monthly_diff is None or monthly_diff.empty:
        print("No budget differences found.")
        return
    
    # Create a static figure with fixed dimensions
    plt.figure(figsize=(10, 8))
    
    # Sum all monthly changes to get total change by category
    if 'Yearly' in monthly_diff.columns:
        # If we have a yearly column, use that
        changes = monthly_diff['Yearly'].copy()
    else:
        # Sum all month columns
        month_cols = [col for col in monthly_diff.columns if col not in ['Categories']]
        changes = monthly_diff[month_cols].sum(axis=1)
    
    # Create a dataframe with Category and total change
    change_df = pd.DataFrame({
        'Category': monthly_diff['Categories'],
        'Change': changes
    })
    
    # Sort by absolute change and get top N categories
    change_df['AbsChange'] = change_df['Change'].abs()
    top_categories = change_df.sort_values('AbsChange', ascending=False).head(top_n)
    
    # Create colors based on change direction
    colors = ['green' if x >= 0 else 'red' for x in top_categories['Change']]
    
    # Create shortened category names for display
    top_categories['Display'] = top_categories['Category'].apply(lambda x: x[:20] + '...' if len(x) > 20 else x)
    
    # Plot the bars
    plt.barh(top_categories['Display'], top_categories['Change'], color=colors)
    
    # Add labels and title
    plt.xlabel('Budget Change ($)')
    plt.ylabel('Category')
    plt.title('Top Budget Changes by Category')
    
    # Add value labels to the bars
    for i, (value, category) in enumerate(zip(top_categories['Change'], top_categories['Display'])):
        # Format value as currency
        formatted_value = f"${abs(value):,.2f}"
        # Position label inside or outside the bar depending on bar length
        if value >= 0:
            plt.text(value + 0.1, i, formatted_value, va='center')
        else:
            plt.text(value - 0.1, i, formatted_value, va='center', ha='right')
    
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    if save:
        # Ensure plots directory exists
        os.makedirs('plots', exist_ok=True)
        plt.savefig('plots/budget_changes.png', dpi=100)
        print(f"Budget changes plot saved to plots/budget_changes.png")
    
    plt.close()

def plot_balance_changes(diff_df, save=True):
    """Plot changes in account balances
    
    Args:
        diff_df: DataFrame with balance differences
        save: Whether to save the plot
    """
    if diff_df is None or diff_df.empty:
        print("No balance differences found.")
        return
        
    # Create a static figure with fixed dimensions
    plt.figure(figsize=(10, 8))
    
    # Sort by absolute difference
    diff_df['AbsDifference'] = diff_df['Difference'].abs()
    diff_df_sorted = diff_df.sort_values('AbsDifference', ascending=False)
    
    # Create colors based on change direction
    colors = ['green' if x >= 0 else 'red' for x in diff_df_sorted['Difference']]
    
    # Create shortened account names for display
    diff_df_sorted['DisplayBank'] = diff_df_sorted['Bank'].apply(lambda x: x[:20] + '...' if len(x) > 20 else x)
    
    # Plot the bars
    plt.barh(diff_df_sorted['DisplayBank'], diff_df_sorted['Difference'], color=colors)
    
    # Add labels and title
    plt.xlabel('Balance Change ($)')
    plt.ylabel('Account')
    plt.title('Account Balance Changes')
    
    # Add value labels to the bars
    for i, (value, account) in enumerate(zip(diff_df_sorted['Difference'], diff_df_sorted['DisplayBank'])):
        # Format value as currency
        formatted_value = f"${abs(value):,.2f}"
        # Position label inside or outside the bar depending on bar length
        if value >= 0:
            plt.text(value + 0.1, i, formatted_value, va='center')
        else:
            plt.text(value - 0.1, i, formatted_value, va='center', ha='right')
    
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    if save:
        # Ensure plots directory exists
        os.makedirs('plots', exist_ok=True)
        plt.savefig('plots/balance_changes.png', dpi=100)
        print(f"Balance changes plot saved to plots/balance_changes.png")
    
    plt.close()

def compare_and_plot_budget_versions(current_file=None, previous_file=None, top_n=10, save=True):
    """Compare and plot differences between budget versions
    
    Args:
        current_file: Path to current budget file (defaults to latest version)
        previous_file: Path to previous budget file (defaults to earliest version with same date pattern)
        top_n: Number of top categories to show in the plots
        save: Whether to save the plots
    """
    # Set up plotting style
    setup_plotting_style()
    
    # If current_file not specified, use latest file
    if current_file is None:
        budget_files = get_budget_versions()
        if budget_files:
            current_file = budget_files[-1]  # Latest file
        else:
            print("No budget files found")
            return
    
    # Load data
    current_data, previous_data, current_file, previous_file = load_budget_versions(current_file, previous_file)
    
    if previous_data is None:
        print(f"No previous version found to compare with {current_file}")
        return
    
    print(f"Comparing budget files:\nCurrent: {current_file}\nPrevious: {previous_file}")
    
    # Compare monthly budgets
    monthly_diff = compare_monthly_budgets(current_data, previous_data)
    if monthly_diff is not None:
        print("Plotting monthly budget changes...")
        plot_monthly_budget_changes(monthly_diff, top_n=top_n, save=save)
    else:
        print("Could not compare monthly budgets")
    
    # Compare balances
    balance_diff = compare_balances(current_data, previous_data)
    if balance_diff is not None:
        print("Plotting balance changes...")
        plot_balance_changes(balance_diff, save=save)
    else:
        print("Could not compare balances")

def load_transaction_versions(current_file, previous_file=None):
    """Load current and previous transaction versions
    
    Args:
        current_file: Path to current transaction file
        previous_file: Path to previous transaction file (if None, will use oldest file with same date pattern)
        
    Returns:
        Tuple of (current_df, previous_df, current_file, previous_file)
    """
    current_df = load_transaction_data(current_file)
    
    if previous_file is None:
        # Extract date pattern from current file and find previous version
        if '_' in current_file:
            parts = current_file.split('_')
            if len(parts) >= 3:
                date_pattern = '_'.join(parts[1:-1])
                transaction_files = get_transaction_versions(date_pattern)
                if len(transaction_files) > 1 and transaction_files[-1] == current_file:
                    previous_file = transaction_files[0]  # Get earliest version
    
    if previous_file and os.path.exists(previous_file):
        previous_df = load_transaction_data(previous_file)
    else:
        previous_df = None
    
    return current_df, previous_df, current_file, previous_file

def compare_transactions(current_df, previous_df):
    """Compare transactions between two versions
    
    Args:
        current_df: Current transactions DataFrame
        previous_df: Previous transactions DataFrame
        
    Returns:
        Dictionary of comparison statistics
    """
    if previous_df is None:
        return None
    
    # Ensure Date is datetime
    if not pd.api.types.is_datetime64_any_dtype(current_df['Date']):
        current_df['Date'] = pd.to_datetime(current_df['Date'])
    if not pd.api.types.is_datetime64_any_dtype(previous_df['Date']):
        previous_df['Date'] = pd.to_datetime(previous_df['Date'])
    
    # Get statistics
    current_stats = {
        'count': len(current_df),
        'total_amount': current_df['Amount'].sum(),
        'expenses': current_df[current_df['Amount'] < 0]['Amount'].sum(),
        'income': current_df[current_df['Amount'] > 0]['Amount'].sum(),
        'categories': current_df['Category'].nunique(),
        'date_range': (current_df['Date'].min(), current_df['Date'].max())
    }
    
    previous_stats = {
        'count': len(previous_df),
        'total_amount': previous_df['Amount'].sum(),
        'expenses': previous_df[previous_df['Amount'] < 0]['Amount'].sum(),
        'income': previous_df[previous_df['Amount'] > 0]['Amount'].sum(),
        'categories': previous_df['Category'].nunique(),
        'date_range': (previous_df['Date'].min(), previous_df['Date'].max())
    }
    
    # Calculate category changes
    current_categories = current_df.groupby('Category')['Amount'].sum().to_dict()
    previous_categories = previous_df.groupby('Category')['Amount'].sum().to_dict()
    
    # Find categories that changed or are new/removed
    all_categories = set(current_categories.keys()) | set(previous_categories.keys())
    category_changes = {}
    
    for category in all_categories:
        current_amount = current_categories.get(category, 0)
        previous_amount = previous_categories.get(category, 0)
        category_changes[category] = current_amount - previous_amount
    
    # Find new transactions in current that weren't in previous
    # This is an approximation - we consider transactions with same date, amount and category as duplicates
    current_df['Transaction_Key'] = current_df.apply(lambda row: f"{row['Date']}_{row['Amount']}_{row['Category']}", axis=1)
    previous_df['Transaction_Key'] = previous_df.apply(lambda row: f"{row['Date']}_{row['Amount']}_{row['Category']}", axis=1)
    
    new_transaction_keys = set(current_df['Transaction_Key']) - set(previous_df['Transaction_Key'])
    new_transactions = current_df[current_df['Transaction_Key'].isin(new_transaction_keys)]
    
    return {
        'current_stats': current_stats,
        'previous_stats': previous_stats,
        'category_changes': category_changes,
        'new_transactions': new_transactions
    }

def plot_transaction_comparison(comparison_data, top_n=10, save=True):
    """Plot transaction comparison visualizations
    
    Args:
        comparison_data: Dictionary with comparison statistics
        top_n: Number of top categories to show
        save: Whether to save the plots
    """
    if comparison_data is None:
        print("No comparison data available to plot")
        return
    
    current_stats = comparison_data['current_stats']
    previous_stats = comparison_data['previous_stats']
    category_changes = comparison_data['category_changes']
    
    # 1. Plot overall statistics comparison
    plt.figure(figsize=(12, 8))
    
    metrics = ['total_amount', 'expenses', 'income']
    labels = ['Total Amount', 'Expenses', 'Income']
    current_values = [current_stats[metric] for metric in metrics]
    previous_values = [previous_stats[metric] for metric in metrics]
    
    x = range(len(metrics))
    width = 0.35
    
    plt.bar([i - width/2 for i in x], previous_values, width, label='Previous', color='blue', alpha=0.7)
    plt.bar([i + width/2 for i in x], current_values, width, label='Current', color='green', alpha=0.7)
    
    # Add labels and title
    plt.title('Transaction Summary Comparison', fontweight='bold', fontsize=16)
    plt.ylabel('Amount ($)')
    plt.xticks(x, labels)
    plt.legend()
    plt.grid(axis='y', alpha=0.3)
    
    # Add value labels to bars
    for i, v in enumerate(previous_values):
        plt.text(i - width/2, v + (100 if v >= 0 else -100), f'${v:.2f}', 
                ha='center', va='bottom' if v >= 0 else 'top', 
                color='blue', fontweight='bold')
    
    for i, v in enumerate(current_values):
        plt.text(i + width/2, v + (100 if v >= 0 else -100), f'${v:.2f}', 
                ha='center', va='bottom' if v >= 0 else 'top', 
                color='green', fontweight='bold')
    
    plt.tight_layout()
    
    if save:
        plt.savefig('plots/transaction_summary_comparison.png', dpi=300, bbox_inches='tight')
    
    plt.show()
    
    # 2. Plot category changes
    # Get top categories by absolute change
    category_change_df = pd.DataFrame({
        'Category': list(category_changes.keys()),
        'Change': list(category_changes.values())
    })
    category_change_df['Abs_Change'] = category_change_df['Change'].abs()
    top_changes = category_change_df.nlargest(top_n, 'Abs_Change')
    
    plt.figure(figsize=(14, 8))
    
    # Define colors based on positive/negative
    colors = ['green' if x >= 0 else 'red' for x in top_changes['Change']]
    
    plt.bar(top_changes['Category'], top_changes['Change'], color=colors)
    
    # Add labels and title
    plt.title('Top Category Amount Changes', fontweight='bold', fontsize=16)
    plt.ylabel('Change Amount ($)')
    plt.xlabel('Category')
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', alpha=0.3)
    
    # Add value labels to bars
    for i, (_, row) in enumerate(top_changes.iterrows()):
        plt.text(i, row['Change'] + (50 if row['Change'] >= 0 else -50), 
                f'${row["Change"]:.2f}', 
                ha='center', va='bottom' if row['Change'] >= 0 else 'top', 
                color='black', fontweight='bold')
    
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    
    plt.tight_layout()
    
    if save:
        plt.savefig('plots/transaction_category_changes.png', dpi=300, bbox_inches='tight')
    
    plt.show()
    
    # 3. Plot new transactions by category
    new_transactions = comparison_data['new_transactions']
    if not new_transactions.empty:
        new_by_category = new_transactions.groupby('Category')['Amount'].sum()
        new_by_category = new_by_category.sort_values()
        
        plt.figure(figsize=(14, 8))
        
        # Define colors based on positive/negative
        colors = ['green' if x >= 0 else 'red' for x in new_by_category]
        
        plt.bar(new_by_category.index, new_by_category, color=colors)
        
        # Add labels and title
        plt.title('New Transactions by Category', fontweight='bold', fontsize=16)
        plt.ylabel('Amount ($)')
        plt.xlabel('Category')
        plt.xticks(rotation=45, ha='right')
        plt.grid(axis='y', alpha=0.3)
        
        # Add value labels to bars
        for i, (cat, val) in enumerate(new_by_category.items()):
            plt.text(i, val + (50 if val >= 0 else -50), 
                    f'${val:.2f}', 
                    ha='center', va='bottom' if val >= 0 else 'top', 
                    color='black', fontweight='bold')
        
        plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        plt.tight_layout()
        
        if save:
            plt.savefig('plots/new_transactions_by_category.png', dpi=300, bbox_inches='tight')
        
        plt.show()

def compare_and_plot_transaction_versions(current_file=None, previous_file=None, top_n=10, save=True):
    """Compare and plot differences between transaction versions
    
    Args:
        current_file: Path to current transaction file (defaults to latest version)
        previous_file: Path to previous transaction file (defaults to earliest version with same date pattern)
        top_n: Number of top categories to show in the plots
        save: Whether to save the plots
    """
    # Set up plotting style
    setup_plotting_style()
    
    # If current_file not specified, use latest file
    if current_file is None:
        transaction_files = get_transaction_versions()
        if transaction_files:
            current_file = transaction_files[-1]  # Latest file
        else:
            print("No transaction files found")
            return
    
    # Load data
    current_df, previous_df, current_file, previous_file = load_transaction_versions(current_file, previous_file)
    
    if previous_df is None:
        print(f"No previous version found to compare with {current_file}")
        return
    
    print(f"Comparing transaction files:\nCurrent: {current_file}\nPrevious: {previous_file}")
    
    # Compare transactions
    comparison_data = compare_transactions(current_df, previous_df)
    if comparison_data is not None:
        print("Plotting transaction comparison...")
        plot_transaction_comparison(comparison_data, top_n=top_n, save=save)
    else:
        print("Could not compare transactions")

if __name__ == "__main__":
    compare_and_plot_budget_versions() 