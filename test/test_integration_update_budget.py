import os
import tempfile
import shutil

import pandas as pd

from BudgetMeeting import update_budget


def create_minimal_budget_xlsx(path: str, year: int):
    # Minimal sheets: Categories, Expenses, Balances, and one category sheet
    # Ensure equal-length columns for DataFrame construction
    categories = {
        'Monthly': [''],
        'Quarterly': [''],
        'Yearly': ['Groceries'],
        'Loan': [''],
    }
    expenses = {
        'Category': ['Groceries'],
        'This Year': [600.0],
        'Next Year': [600.0],
    }
    balances = {
        'Date': [pd.Timestamp(year, 1, 1)],
        'Balance': [1000.0],
    }
    groceries = {
        # Two rows: one in Jan and one in Dec to ensure EOY projection coverage
        'Date': [f"01/15/{year}", f"12/31/{year}"],
        'Desc.': ['Planned Groceries', 'EOY Groceries'],
        'This Year': [50.0, 0.0],
        'R': ['', ''],
        'Next Year': [50.0, 50.0],
        'Note': ['', ''],
    }

    with pd.ExcelWriter(path, engine='xlsxwriter') as writer:
        pd.DataFrame(categories).to_excel(writer, sheet_name='Categories', index=False)
        pd.DataFrame(expenses).to_excel(writer, sheet_name='Expenses', index=False)
        pd.DataFrame(balances).to_excel(writer, sheet_name='Balances', index=False)
        pd.DataFrame(groceries).to_excel(writer, sheet_name='Groceries', index=False)


def test_update_budget_end_to_end_creates_expected_sheets(tmp_path):
    year = 2024
    # Work in an isolated temp directory because update_budget writes backups/archives
    with tempfile.TemporaryDirectory() as tmpdir:
        cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            budget_path = os.path.join(tmpdir, 'Budget_Test.xlsx')
            create_minimal_budget_xlsx(budget_path, year)

            # No transactions provided (None)
            update_budget(budget_path, None, year)

            # Validate output workbook
            xls = pd.ExcelFile(budget_path)
            sheets = set(xls.sheet_names)

            # Must include core output sheets
            expected = {'Projection', 'Monthly', 'Diffs', 'Q Summary', 'Y Summary', 'Yearly Remaining', 'Expenses', 'Categories', 'Balances'}
            assert expected.issubset(sheets)

            # Validate Projection required columns
            df_proj = xls.parse('Projection')
            for col in ['Date', 'Desc.', 'Amount', 'Category', 'Balance', 'Note']:
                assert col in df_proj.columns

            # Validate Monthly sheet has Categories and at least January column
            df_monthly = xls.parse('Monthly')
            assert 'Categories' in df_monthly.columns
            assert any('January' in c for c in df_monthly.columns)

            # Validate Yearly Remaining has 5 years starting from current year
            df_remaining = xls.parse('Yearly Remaining')
            expected_year_cols = [str(year + i) for i in range(5)]
            for col in expected_year_cols:
                assert col in df_remaining.columns

        finally:
            os.chdir(cwd)


