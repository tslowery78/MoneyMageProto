#!/usr/bin/env python3
import argparse
from visualization import (
    setup_plotting_style, load_transaction_data, load_budget_data,
    plot_monthly_spending_by_category, plot_spending_trend_over_time,
    plot_income_vs_expenses, plot_balance_projection, plot_spending_by_account,
    plot_monthly_budget_vs_actual, generate_all_plots
)
from budget_comparison import (
    compare_and_plot_budget_versions, get_budget_versions, get_transaction_versions,
    compare_and_plot_transaction_versions
)

def main():
    """Main CLI function to generate plots"""
    parser = argparse.ArgumentParser(description='Generate financial plots from transaction and budget data')
    
    # Standard visualization options
    parser.add_argument('--all', action='store_true', help='Generate all plots')
    parser.add_argument('--no-save', action='store_true', help='Do not save plots to files')
    parser.add_argument('--transactions', type=str, default='transactions.xlsx', 
                        help='Path to transactions Excel file (default: transactions.xlsx)')
    parser.add_argument('--budget', type=str, default='Budget_2025.xlsx', 
                        help='Path to budget Excel file (default: Budget_2025.xlsx)')
    
    # Specific plot types
    parser.add_argument('--top-spending', action='store_true', help='Plot top spending categories')
    parser.add_argument('--top-n', type=int, default=10, help='Number of top categories to show (default: 10)')
    
    parser.add_argument('--spending-trend', action='store_true', help='Plot spending trend over time')
    parser.add_argument('--categories', type=str, nargs='+', 
                        help='Specific categories to include in the spending trend plot')
    
    parser.add_argument('--income-vs-expenses', action='store_true', help='Plot income vs expenses')
    
    parser.add_argument('--balance-projection', action='store_true', help='Plot balance projection')
    
    parser.add_argument('--by-account', action='store_true', help='Plot spending by account')
    
    parser.add_argument('--budget-vs-actual', action='store_true', help='Plot budget vs actual for specific categories')
    parser.add_argument('--budget-categories', type=str, nargs='+', 
                        help='Categories to include in budget vs actual plot')
    
    # Budget comparison options
    parser.add_argument('--compare-budgets', action='store_true', 
                        help='Compare and visualize differences between budget versions')
    parser.add_argument('--current-budget', type=str, 
                        help='Path to current budget file (defaults to latest version)')
    parser.add_argument('--previous-budget', type=str, 
                        help='Path to previous budget file (defaults to earliest version with same date pattern)')
    
    # Transaction comparison options
    parser.add_argument('--compare-transactions', action='store_true',
                        help='Compare and visualize differences between transaction versions')
    parser.add_argument('--current-transactions', type=str,
                       help='Path to current transactions file (defaults to latest version)')
    parser.add_argument('--previous-transactions', type=str,
                       help='Path to previous transactions file (defaults to earliest version with same date pattern)')
    
    parser.add_argument('--list-versions', action='store_true',
                        help='List available budget and transaction file versions')
    
    args = parser.parse_args()
    
    # List available versions if requested
    if args.list_versions:
        budget_versions = get_budget_versions()
        transaction_versions = get_transaction_versions()
        
        print("Available Budget Versions:")
        for file in budget_versions:
            print(f"  {file}")
        
        print("\nAvailable Transaction Versions:")
        for file in transaction_versions:
            print(f"  {file}")
        
        return
    
    # Handle budget comparison if requested
    if args.compare_budgets:
        print("Comparing budget versions...")
        compare_and_plot_budget_versions(
            current_file=args.current_budget,
            previous_file=args.previous_budget,
            top_n=args.top_n,
            save=not args.no_save
        )
        return
    
    # Handle transaction comparison if requested
    if args.compare_transactions:
        print("Comparing transaction versions...")
        compare_and_plot_transaction_versions(
            current_file=args.current_transactions,
            previous_file=args.previous_transactions,
            top_n=args.top_n,
            save=not args.no_save
        )
        return
    
    # Set up plotting style
    setup_plotting_style()
    
    # Load data
    transactions_df = load_transaction_data(args.transactions)
    budget_data = load_budget_data(args.budget)
    
    save = not args.no_save
    
    # Generate all plots if requested or if no specific plots are requested
    if args.all or not any([args.top_spending, args.spending_trend, args.income_vs_expenses, 
                           args.balance_projection, args.by_account, args.budget_vs_actual]):
        print("Generating all plots...")
        generate_all_plots()
    else:
        # Generate specific plots as requested
        if args.top_spending:
            print(f"Generating top {args.top_n} spending categories plot...")
            plot_monthly_spending_by_category(transactions_df, top_n=args.top_n, save=save)
        
        if args.spending_trend:
            print("Generating spending trend plot...")
            plot_spending_trend_over_time(transactions_df, top_categories=args.categories, save=save)
        
        if args.income_vs_expenses:
            print("Generating income vs expenses plot...")
            plot_income_vs_expenses(transactions_df, save=save)
        
        if args.balance_projection:
            print("Generating balance projection plot...")
            plot_balance_projection(budget_data, save=save)
        
        if args.by_account:
            print("Generating spending by account plot...")
            plot_spending_by_account(transactions_df, save=save)
        
        if args.budget_vs_actual:
            if args.budget_categories:
                for category in args.budget_categories:
                    print(f"Generating budget vs actual plot for {category}...")
                    plot_monthly_budget_vs_actual(budget_data, transactions_df, category, save=save)
            else:
                # Default to some important categories
                important_categories = ['Groceries', 'Restaurant', 'Mortgage', 'Auto - Gas', 'Home Supplies']
                for category in important_categories:
                    print(f"Generating budget vs actual plot for {category}...")
                    plot_monthly_budget_vs_actual(budget_data, transactions_df, category, save=save)
    
    print("Plot generation completed!")

if __name__ == "__main__":
    main() 