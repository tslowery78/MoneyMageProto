import os
import sys
import io
import shutil
import tempfile
import datetime
from contextlib import redirect_stdout

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Optional, Tuple


# Ensure project root is on sys.path when running via `streamlit run gui/app.py`
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from BudgetMeeting import update_budget, BudgetMeeting as run_budget_meeting  # noqa: E402
from transactions import get_transactions, update_auto_categories  # noqa: E402


def file_exists(path: str) -> bool:
    try:
        return bool(path) and os.path.exists(path)
    except Exception:
        return False


def run_budget_meeting_live(budget_xlsx: str, transactions_xlsx: str, year: int) -> str:
    """Run the full BudgetMeeting flow and return captured logs.

    This will import new transactions, update the budget, and update auto-categories.
    It mutates the budget file and creates backups as implemented in the core scripts.
    """
    log_buffer = io.StringIO()
    with redirect_stdout(log_buffer):
        # Call the end-to-end function from BudgetMeeting.py
        run_budget_meeting(budget_xlsx, transactions_xlsx, year)
    return log_buffer.getvalue()


def run_budget_meeting_preview(original_budget_xlsx: str, transactions_xlsx: str, year: int) -> Tuple[str, str]:
    """Run a preview/dry-run by copying the budget to a temp file and updating that.

    Returns: (preview_budget_path, logs)
    """
    # Copy to a temp file under archive/ for easy discovery
    os.makedirs(os.path.join(PROJECT_ROOT, "archive"), exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    preview_path = os.path.join(PROJECT_ROOT, "archive", f"PREVIEW_{ts}_" + os.path.basename(original_budget_xlsx))
    shutil.copyfile(original_budget_xlsx, preview_path)

    log_buffer = io.StringIO()
    with redirect_stdout(log_buffer):
        update_budget(budget_xlsx=preview_path, transactions=_get_transactions_df(transactions_xlsx), this_year=year)
    return preview_path, log_buffer.getvalue()


def _get_transactions_df(transactions_xlsx: str) -> Optional[dict]:
    """Load transactions.xlsx into dict format expected by update_budget (or return None).

    update_budget expects a dict or None. Here we read the Transactions sheet if present.
    """
    if not file_exists(transactions_xlsx):
        return None
    try:
        df = pd.read_excel(transactions_xlsx, sheet_name="Transactions")
        df.fillna("", inplace=True)
        # Normalize Date column to date objects if present
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
        return df.to_dict("list")
    except Exception:
        return None


def read_sheet(xlsx_path: str, sheet_name: str) -> pd.DataFrame | None:
    try:
        return pd.read_excel(xlsx_path, sheet_name=sheet_name)
    except Exception:
        return None


def read_q_summary_sections(xlsx_path: str) -> dict[int, pd.DataFrame] | None:
    """Parse the 'Q Summary' sheet into 4 separate quarter DataFrames.

    The writer lays out sections as blocks with a title row 'Quarter X Summary',
    followed by a header row ['Category','Planned','Spent','Remaining'], then rows.
    """
    try:
        raw = pd.read_excel(xlsx_path, sheet_name='Q Summary', header=None)
    except Exception:
        return None

    sections: dict[int, pd.DataFrame] = {}
    i = 0
    n = len(raw)
    while i < n:
        cell = raw.iat[i, 0] if 0 in raw.columns else None
        if isinstance(cell, str) and cell.strip().startswith('Quarter'):
            # Extract quarter number
            try:
                q_num = int(cell.split()[1])
            except Exception:
                q_num = None
            # Header is next row
            header_row = i + 1
            if header_row < n:
                headers = raw.iloc[header_row].tolist()
                # Collect data rows until next title or empty header repeat
                data_start = header_row + 1
                data_rows = []
                r = data_start
                while r < n:
                    first = raw.iat[r, 0] if 0 in raw.columns else None
                    # Stop if next section title encountered
                    if isinstance(first, str) and first.strip().startswith('Quarter'):
                        break
                    # Stop if completely empty row
                    if pd.isna(first) and all(pd.isna(x) for x in raw.iloc[r].tolist()):
                        break
                    data_rows.append(raw.iloc[r].tolist())
                    r += 1
                if q_num is not None and headers:
                    df = pd.DataFrame(data_rows, columns=[str(h) for h in headers])
                    # Trim to expected columns if present
                    keep = [c for c in ['Category', 'Planned', 'Spent', 'Remaining'] if c in df.columns]
                    df = df[keep] if keep else df
                    # Drop rows with all NaNs in numeric cols
                    for col in ['Planned', 'Spent', 'Remaining']:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    if any(c in df.columns for c in ['Planned', 'Spent', 'Remaining']):
                        mask = None
                        for col in ['Planned', 'Spent', 'Remaining']:
                            if col in df.columns:
                                mask = df[col].notna() if mask is None else (mask | df[col].notna())
                        if mask is not None:
                            df = df[mask]
                    sections[q_num] = df.reset_index(drop=True)
                i = r
                continue
        i += 1

    # Ensure we return quarters 1..4 keys if found
    return sections if sections else None


def show_top_spending_chart(transactions_xlsx: str, top_n: int = 10):
    if not file_exists(transactions_xlsx):
        st.info("Transactions file not found.")
        return
    try:
        df = pd.read_excel(transactions_xlsx, sheet_name="Transactions")
    except Exception:
        st.info("Unable to read Transactions sheet.")
        return
    if "Amount" not in df.columns or "Category" not in df.columns:
        st.info("Transactions sheet missing required columns.")
        return
    df = df.copy()
    # Expenses negative, take absolute for magnitude
    top = df[df["Amount"] < 0].groupby("Category")["Amount"].sum().abs().nlargest(top_n)
    if top.empty:
        st.info("No expense data to chart.")
        return
    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))
    # Assign hue explicitly to avoid seaborn deprecation
    sns.barplot(x=top.values, y=top.index, hue=top.index, palette="viridis", legend=False, ax=ax)
    ax.set_title(f"Top {top_n} Categories by Spending")
    ax.set_xlabel("Amount ($)")
    ax.set_ylabel("Category")
    st.pyplot(fig, clear_figure=True)


def show_balance_projection_chart(budget_xlsx: str):
    df = read_sheet(budget_xlsx, "Projection")
    if df is None or "Date" not in df.columns or "Balance" not in df.columns:
        st.info("Projection sheet not found or missing columns.")
        return
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date", "Balance"])  # keep valid rows
    if df.empty:
        st.info("No projection data to chart.")
        return
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(df["Date"], df["Balance"], marker="o", linewidth=2, color="steelblue")
    ax.axhline(y=0, color="red", linestyle="--", alpha=0.5)
    ax.set_title("Projected Account Balance Over Time")
    ax.set_xlabel("Date")
    ax.set_ylabel("Balance ($)")
    fig.autofmt_xdate()
    st.pyplot(fig, clear_figure=True)


def show_budget_vs_actual_chart(budget_xlsx: str, transactions_xlsx: str, category: str):
    monthly = read_sheet(budget_xlsx, "Monthly")
    if monthly is None or monthly.empty or "Categories" not in monthly.columns:
        st.info("Monthly sheet not available for budget vs actual chart.")
        return
    row = monthly[monthly["Categories"] == category]
    if row.empty:
        st.info(f"Category '{category}' not found in Monthly sheet.")
        return
    # Columns excluding 'Categories' and 'Yearly'
    months = [c for c in monthly.columns if c not in ["Categories", "Yearly"]]
    budget_vals = row[months].values[0]

    # Load transactions
    if not file_exists(transactions_xlsx):
        st.info("Transactions file not found for actuals.")
        return
    try:
        tdf = pd.read_excel(transactions_xlsx, sheet_name="Transactions")
    except Exception:
        st.info("Unable to read Transactions sheet for actuals.")
        return
    if "Date" not in tdf.columns or "Amount" not in tdf.columns or "Category" not in tdf.columns:
        st.info("Transactions sheet missing required columns.")
        return
    tdf = tdf.copy()
    tdf["Date"] = pd.to_datetime(tdf["Date"], errors="coerce")
    tdf["Month"] = tdf["Date"].dt.strftime("%B %Y")
    actuals = []
    # Build actuals aligned to months
    for m in months:
        mdf = tdf[(tdf["Category"] == category) & (tdf["Month"] == m)]
        total = mdf["Amount"].sum()
        # If budget is negative (expense), compare magnitudes as positive
        idx = months.index(m)
        b = budget_vals[idx]
        if pd.notna(b) and b < 0:
            actuals.append(abs(total))
        else:
            actuals.append(total)

    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    x = range(len(months))
    width = 0.4
    # Convert negative budgets to positive for display of expenses
    plot_budget = [abs(v) if pd.notna(v) and v < 0 else (0 if pd.isna(v) else v) for v in budget_vals]
    ax.bar([i - width/2 for i in x], plot_budget, width, label="Budgeted", color="#1f77b4", alpha=0.75)
    ax.bar([i + width/2 for i in x], actuals, width, label="Actual", color="#2ca02c", alpha=0.75)
    ax.set_title(f"Monthly Budget vs Actual: {category}")
    ax.set_xlabel("Month")
    ax.set_ylabel("Amount ($)")
    ax.set_xticks(list(x))
    ax.set_xticklabels([m.split(" ")[0] for m in months], rotation=0)
    ax.legend()
    st.pyplot(fig, clear_figure=True)


def main():
    st.set_page_config(page_title="MoneyMage Budget Meeting", layout="wide")
    st.title("MoneyMage Budget Meeting")
    st.caption("Run updates, preview diffs, and visualize your budget.")

    # Sidebar controls
    with st.sidebar:
        st.header("Configuration")
        default_budget = os.path.join(PROJECT_ROOT, "Budget_2025.xlsx")
        default_transactions = os.path.join(PROJECT_ROOT, "transactions.xlsx")

        budget_xlsx = st.text_input("Budget file", value=default_budget)
        transactions_xlsx = st.text_input("Transactions file", value=default_transactions)
        year = st.number_input("Budget year", value=datetime.date.today().year, step=1)

        run_live = st.button("Run Budget Meeting (Live End-to-End)", type="primary")
        run_preview = st.button("Preview Update Budget (Dry Run)")

        st.markdown("---")
        st.header("Quick Actions")
        import_new = st.button("Import + Auto-categorize Transactions")
        update_auto = st.button("Update Auto-Categories from Reconciled")
        open_budget = st.button("Open Budget in Finder")

    # Session state for last result
    if "last_budget_path" not in st.session_state:
        st.session_state["last_budget_path"] = budget_xlsx if file_exists(budget_xlsx) else ""
    if "last_logs" not in st.session_state:
        st.session_state["last_logs"] = ""

    # Handle actions
    if run_live:
        if not file_exists(budget_xlsx):
            st.error("Budget file not found.")
        else:
            with st.spinner("Running budget meeting (live end-to-end)..."):
                logs = run_budget_meeting_live(budget_xlsx, transactions_xlsx, int(year))
            st.session_state["last_budget_path"] = budget_xlsx
            st.session_state["last_logs"] = logs
            st.success("Budget updated.")

    if run_preview:
        if not file_exists(budget_xlsx):
            st.error("Budget file not found.")
        else:
            with st.spinner("Running preview (dry run)..."):
                preview_path, logs = run_budget_meeting_preview(budget_xlsx, transactions_xlsx, int(year))
            st.session_state["last_budget_path"] = preview_path
            st.session_state["last_logs"] = logs
            st.success(f"Preview complete. Opened: {os.path.basename(preview_path)}")

    if import_new:
        with st.spinner("Importing and categorizing new transactions..."):
            buf = io.StringIO()
            with redirect_stdout(buf):
                try:
                    _ = get_transactions(transactions_xlsx)
                except Exception as e:
                    print(f"Error importing transactions: {e}")
            st.session_state["last_logs"] = buf.getvalue() + "\n" + st.session_state.get("last_logs", "")
        st.success("Transactions imported. See logs for details.")

    if update_auto:
        with st.spinner("Updating auto-categories from reconciled transactions..."):
            buf = io.StringIO()
            with redirect_stdout(buf):
                try:
                    update_auto_categories(transactions_xlsx)
                except Exception as e:
                    print(f"Error updating auto-categories: {e}")
            st.session_state["last_logs"] = buf.getvalue() + "\n" + st.session_state.get("last_logs", "")
        st.success("Auto-categories updated.")

    if open_budget and file_exists(st.session_state["last_budget_path"]):
        try:
            # macOS open
            os.system(f"open '{st.session_state['last_budget_path']}'")
        except Exception:
            pass

    # Layout: Logs + Tabs
    with st.expander("Show Logs", expanded=False):
        st.code(st.session_state.get("last_logs", ""))

    tabs = st.tabs([
        "Overview", "Diffs", "Quarterly", "Yearly", "Yearly Remaining", "Projection", "Monthly", "Categories", "Balances", "Charts"
    ])

    budget_to_view = st.session_state.get("last_budget_path")
    if not file_exists(budget_to_view):
        st.warning("Select a budget file and run Live or Preview to populate results.")
        return

    # Overview
    with tabs[0]:
        st.subheader("File")
        st.write(budget_to_view)
        try:
            xls = pd.ExcelFile(budget_to_view)
            st.subheader("Sheets")
            st.write(xls.sheet_names)
        except Exception as e:
            st.error(f"Unable to read budget file: {e}")

    # Helper to sanitize dfs for Streamlit (Arrow serialization safety)
    def sanitize_df_for_streamlit(df: pd.DataFrame) -> pd.DataFrame:
        safe = df.copy()
        # Ensure all column names are strings
        safe.columns = [str(c) for c in safe.columns]
        # Replace problematic mixed-type object columns by casting to string where needed
        for col in safe.columns:
            if safe[col].dtype == 'O':
                # If the column mixes numbers/strings/None, convert to string uniformly
                if not (safe[col].map(type).nunique() == 1 and safe[col].map(type).iloc[0] in (str, bytes)):
                    safe[col] = safe[col].astype(str)
        return safe

    # Diffs
    with tabs[1]:
        df = read_sheet(budget_to_view, "Diffs")
        if df is not None and not df.empty:
            st.dataframe(sanitize_df_for_streamlit(df), use_container_width=True)
        else:
            st.info("No diffs available.")

    # Quarterly
    with tabs[2]:
        st.subheader("Quarterly Overview")
        # Try to parse into separate quarters
        q_sections = read_q_summary_sections(budget_to_view)
        if q_sections:
            q_tabs = st.tabs([f"Q{q}" for q in sorted(q_sections.keys())])
            for idx, q in enumerate(sorted(q_sections.keys())):
                with q_tabs[idx]:
                    qdf = q_sections[q]
                    if qdf is None or qdf.empty:
                        st.info(f"No data for Q{q}.")
                        continue
                    # KPIs
                    planned = qdf['Planned'].sum() if 'Planned' in qdf.columns else 0.0
                    spent = qdf['Spent'].sum() if 'Spent' in qdf.columns else 0.0
                    remaining = qdf['Remaining'].sum() if 'Remaining' in qdf.columns else planned - spent
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Total Planned", f"${planned:,.0f}")
                    c2.metric("Total Spent", f"${spent:,.0f}")
                    c3.metric("Remaining", f"${remaining:,.0f}")

                    # Leaderboard table
                    st.markdown("#### Categories")
                    # Add variance column if possible
                    if all(c in qdf.columns for c in ['Planned', 'Spent']):
                        qdf = qdf.copy()
                        qdf['Variance'] = qdf['Planned'] - qdf['Spent']
                    st.dataframe(sanitize_df_for_streamlit(qdf), use_container_width=True, height=360)

                    # Bar chart: Planned vs Spent per category
                    if all(c in qdf.columns for c in ['Category', 'Planned', 'Spent']):
                        melt_df = qdf.melt(id_vars='Category', value_vars=['Planned', 'Spent'],
                                           var_name='Type', value_name='Amount')
                        # Keep top 20 by Planned magnitude for readability
                        if len(qdf) > 20:
                            top_cats = qdf.sort_values('Planned', ascending=False).head(20)['Category']
                            melt_df = melt_df[melt_df['Category'].isin(top_cats)]
                        fig, ax = plt.subplots(figsize=(10, 6))
                        sns.barplot(data=melt_df, x='Amount', y='Category', hue='Type', palette=['#1f77b4', '#d62728'], ax=ax)
                        ax.set_title(f"Q{q} Planned vs Spent by Category")
                        ax.set_xlabel("Amount ($)")
                        ax.set_ylabel("Category")
                        st.pyplot(fig, clear_figure=True)
        else:
            # Fallback to raw sheet if parsing fails
            df = read_sheet(budget_to_view, "Q Summary")
            if df is not None and not df.empty:
                st.dataframe(sanitize_df_for_streamlit(df), use_container_width=True)
            else:
                st.info("Quarterly summary not available.")

    # Yearly
    with tabs[3]:
        df = read_sheet(budget_to_view, "Y Summary")
        if df is not None and not df.empty:
            st.dataframe(sanitize_df_for_streamlit(df), use_container_width=True)
        else:
            st.info("Yearly summary not available.")

    # Yearly Remaining
    with tabs[4]:
        df = read_sheet(budget_to_view, "Yearly Remaining")
        if df is not None and not df.empty:
            st.dataframe(sanitize_df_for_streamlit(df), use_container_width=True)
        else:
            st.info("Yearly Remaining not available.")

    # Projection
    with tabs[5]:
        df = read_sheet(budget_to_view, "Projection")
        if df is not None and not df.empty:
            st.dataframe(sanitize_df_for_streamlit(df), use_container_width=True, height=400)
        else:
            st.info("Projection not available.")

    # Monthly
    with tabs[6]:
        df = read_sheet(budget_to_view, "Monthly")
        if df is not None and not df.empty:
            st.dataframe(sanitize_df_for_streamlit(df), use_container_width=True, height=400)
        else:
            st.info("Monthly sheet not available.")

    # Categories
    with tabs[7]:
        df = read_sheet(budget_to_view, "Categories")
        if df is not None and not df.empty:
            st.dataframe(sanitize_df_for_streamlit(df), use_container_width=True)
        else:
            st.info("Categories sheet not available.")

    # Balances
    with tabs[8]:
        df = read_sheet(budget_to_view, "Balances")
        if df is not None and not df.empty:
            st.dataframe(sanitize_df_for_streamlit(df), use_container_width=True)
        else:
            st.info("Balances sheet not available.")

    # Charts
    with tabs[9]:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Top Spending Categories")
            show_top_spending_chart(transactions_xlsx)
        with c2:
            st.subheader("Balance Projection")
            show_balance_projection_chart(budget_to_view)

        st.markdown("---")
        st.subheader("Budget vs Actual by Category")
        monthly_df = read_sheet(budget_to_view, "Monthly")
        categories = []
        if monthly_df is not None and not monthly_df.empty and "Categories" in monthly_df.columns:
            categories = [c for c in monthly_df["Categories"].dropna().tolist() if c != "Monthly Total"]
        selected_cat = st.selectbox("Choose a category", options=categories)
        if selected_cat:
            show_budget_vs_actual_chart(budget_to_view, transactions_xlsx, selected_cat)


if __name__ == "__main__":
    main()


