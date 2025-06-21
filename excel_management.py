import pandas as pd
import datetime
from utilities import make_dict_list_same_len, dates_to_str, remove_list_blanks_nonzero
import os
import shutil
from xlsxwriter.utility import xl_col_to_name


def write_transactions_xlsx(transactions_input, new_transactions):
    """Function to write transactions into an xlsx"""

    os.makedirs('archive/', exist_ok=True)
    back_up_xls = 'transactions' \
                  + f'_{datetime.date.today().month}_{datetime.date.today().day}_{datetime.date.today().year}_' \
                    f'{datetime.datetime.today().second}.xlsx'
    shutil.copy('transactions.xlsx', f'archive/{back_up_xls}')

    # Create transactions dataframe and output into the Transactions sheet
    dates_to_str(transactions_input)
    df = pd.DataFrame.from_dict(transactions_input)
    dates_to_str(new_transactions)
    df_new_transactions = pd.DataFrame.from_dict(new_transactions)
    df.sort_values('Date', inplace=True)
    df_new_transactions.sort_values('Date', inplace=True)
    writer = pd.ExcelWriter('transactions.xlsx', engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Transactions', index=False, na_rep='')
    df_new_transactions.to_excel(writer, sheet_name='Imported', index=False, na_rep='')

    # Format the xls
    dfs = [df, df_new_transactions]
    sheet_names = ['Transactions', 'Imported']
    for i, this_df in enumerate(dfs):
        make_xls_pretty(writer, this_df, sheet_names[i])

    writer.close()


def make_xls_pretty(writer, df, sheet_name, **kwargs):
    """Function to make the sheets readable"""

    # Get the xlsxwriter workbook and worksheet objects
    workbook = writer.book

    # Set a currency number format for an amount column
    num_format = workbook.add_format({'num_format': '#,###.00'})
    date_format = workbook.add_format({'num_format': 'mm/dd/yyyy'})
    int_format = workbook.add_format({'num_format': '#,###'})

    # For each column in each sheet set the appropriate column width
    date_columns = ['Date', 'End of Month']
    int_columns = ['Quarter', 'Month']
    num_columns = ['This Year', 'Spent', 'Remaining', 'Next Year', 'Actual', 'Planned', 'Difference', 'Payment',
                   'Reconciled', 'Amount', 'Balance']
    date_dict = {'Dates': [date_columns, date_format], 'Num': [num_columns, num_format],
                 'Int': [int_columns, int_format]}

    if 'all' in kwargs.keys():
        for column in df:
            col_idx = df.columns.get_loc(column)
            if column == 'Categories':
                column_length = max(df[column].astype(str).map(len).max(), len(column))
            else:
                column_length = 17
            writer.sheets[sheet_name].set_column(col_idx, col_idx, column_length, num_format)
        return

    for column in df:
        column_length = max(df[column].astype(str).map(len).max(), len(column)) + 5
        col_idx = df.columns.get_loc(column)
        for key, key_list in date_dict.items():
            these_columns = key_list[0]
            this_format = key_list[1]
            if column in these_columns:
                writer.sheets[sheet_name].set_column(col_idx, col_idx, column_length, this_format)
                break
        writer.sheets[sheet_name].set_column(col_idx, col_idx, column_length)


def write_summary_sheet_with_links(writer, df, sheet_name, nav_links=None, nav_col=None):
    """Writes a summary DataFrame to a sheet with hyperlinks for the Category column."""
    workbook = writer.book
    worksheet = workbook.add_worksheet(sheet_name)
    writer.sheets[sheet_name] = worksheet

    # Add formats
    header_format = workbook.add_format({'bold': True, 'bottom': 1})
    num_format = workbook.add_format({'num_format': '#,###.00'})
    url_format = workbook.add_format({'color': 'blue', 'underline': 1})

    # Write header
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_format)

    # Write data rows
    cat_col_idx = df.columns.get_loc('Category')
    for row_num, row_data in enumerate(df.itertuples(index=False), 1):
        for col_num, cell_data in enumerate(row_data):
            if col_num == cat_col_idx:
                url = f"internal:'{cell_data}'!A1"
                worksheet.write_url(row_num, col_num, url, cell_format=url_format, string=cell_data)
            else:
                if isinstance(cell_data, (int, float)):
                    if pd.isna(cell_data):
                        worksheet.write_blank(row_num, col_num, None)
                    else:
                        worksheet.write_number(row_num, col_num, cell_data, num_format)
                else:
                    worksheet.write(row_num, col_num, cell_data)

    # Add navigation links if provided
    if nav_links and nav_col:
        for i, link_sheet in enumerate(nav_links, start=1):
            cell = f'{nav_col}{i}'
            url = f"internal:'{link_sheet}'!A1"
            worksheet.write_url(cell, url, cell_format=url_format, string=link_sheet)

    # Auto-adjust column widths
    for i, col in enumerate(df.columns):
        column_len = len(col)
        max_len = df[col].astype(str).map(len).max()
        if pd.notna(max_len):
            column_len = max(column_len, max_len)
        worksheet.set_column(i, i, column_len + 2)
    
    # Add a bar chart if 'Planned' and 'Spent' columns exist
    if 'Planned' in df.columns and 'Spent' in df.columns and not df.empty:
        chart = workbook.add_chart({'type': 'column'})
        num_rows = len(df)
        
        # Get column indexes
        cat_col_idx = df.columns.get_loc('Category')
        plan_col_idx = df.columns.get_loc('Planned')
        spent_col_idx = df.columns.get_loc('Spent')

        # Define data series references
        categories_ref = f"='{sheet_name}'!${xl_col_to_name(cat_col_idx)}$2:${xl_col_to_name(cat_col_idx)}${num_rows + 1}"
        planned_ref = f"='{sheet_name}'!${xl_col_to_name(plan_col_idx)}$2:${xl_col_to_name(plan_col_idx)}${num_rows + 1}"
        spent_ref = f"='{sheet_name}'!${xl_col_to_name(spent_col_idx)}$2:${xl_col_to_name(spent_col_idx)}${num_rows + 1}"
        
        # Add series to the chart
        chart.add_series({
            'name': 'Planned',
            'categories': categories_ref,
            'values':     planned_ref,
            'fill':       {'color': 'green'},
        })
        chart.add_series({
            'name':       'Spent',
            'values':     spent_ref,
            'fill':       {'color': 'red'},
        })
        
        # Configure chart
        chart.set_title({'name': f'{sheet_name} Planned vs. Spent'})
        chart.set_x_axis({'name': 'Category', 'text_axis': True, 'num_font': {'rotation': 45}})
        chart.set_y_axis({'name': 'Amount ($)'})
        chart.set_size({'width': 720, 'height': 576})
        
        # Insert chart into the worksheet
        chart_col = 'H'
        if nav_col:
            chart_col_idx = ord(nav_col[0]) - ord('A') + 2
            chart_col = xl_col_to_name(chart_col_idx)
        worksheet.insert_chart(f'{chart_col}2', chart)


def write_sheet_with_all_category_links(writer, df, sheet_name, category_sheets, nav_links=None, nav_col=None):
    """Writes a DataFrame to a sheet, turning any cell that is a category name into a hyperlink."""
    workbook = writer.book
    worksheet = workbook.add_worksheet(sheet_name)
    writer.sheets[sheet_name] = worksheet

    # Add formats
    header_format = workbook.add_format({'bold': True, 'bottom': 1})
    url_format = workbook.add_format({'color': 'blue', 'underline': 1})

    # Write header
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_format)

    # Write data rows
    for row_num, row_data in enumerate(df.itertuples(index=False), 1):
        for col_num, cell_data in enumerate(row_data):
            if isinstance(cell_data, str) and cell_data in category_sheets:
                url = f"internal:'{cell_data}'!A1"
                worksheet.write_url(row_num, col_num, url, cell_format=url_format, string=cell_data)
            else:
                if isinstance(cell_data, (int, float)):
                    if pd.isna(cell_data):
                        worksheet.write_blank(row_num, col_num, None)
                    else:
                        worksheet.write_number(row_num, col_num, cell_data)
                else:
                    worksheet.write(row_num, col_num, cell_data)

    # Add navigation links if provided
    if nav_links and nav_col:
        for i, link_sheet in enumerate(nav_links, start=1):
            cell = f'{nav_col}{i}'
            url = f"internal:'{link_sheet}'!A1"
            worksheet.write_url(cell, url, cell_format=url_format, string=link_sheet)

    # Auto-adjust column widths
    for i, col in enumerate(df.columns):
        column_len = len(col)
        max_len = df[col].astype(str).map(len).max()
        if pd.notna(max_len):
            column_len = max(column_len, max_len)
        worksheet.set_column(i, i, column_len + 2)


def write_sheet_with_nav_panel(writer, df, sheet_name, nav_links, nav_col):
    """Writes a DataFrame to a sheet and adds a navigation panel."""
    workbook = writer.book
    worksheet = workbook.add_worksheet(sheet_name)
    writer.sheets[sheet_name] = worksheet

    # Add formats
    header_format = workbook.add_format({'bold': True, 'bottom': 1})
    num_format = workbook.add_format({'num_format': '#,###.00'})
    date_format = workbook.add_format({'num_format': 'mm/dd/yyyy'})
    url_format = workbook.add_format({'color': 'blue', 'underline': 1})

    # Write header
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_format)

    # Write data rows
    for row_num, row_data in enumerate(df.itertuples(index=False), 1):
        for col_num, cell_data in enumerate(row_data):
            if isinstance(cell_data, datetime.date):
                worksheet.write_datetime(row_num, col_num, cell_data, date_format)
            elif isinstance(cell_data, (int, float)):
                if pd.isna(cell_data):
                    worksheet.write_blank(row_num, col_num, None)
                else:
                    worksheet.write_number(row_num, col_num, cell_data, num_format)
            else:
                worksheet.write(row_num, col_num, cell_data)

    # Add navigation links
    if nav_links and nav_col:
        for i, link_sheet in enumerate(nav_links, start=1):
            cell = f'{nav_col}{i}'
            url = f"internal:'{link_sheet}'!A1"
            worksheet.write_url(cell, url, cell_format=url_format, string=link_sheet)

    # Auto-adjust column widths
    for i, col in enumerate(df.columns):
        column_len = len(col)
        max_len = df[col].astype(str).map(len).max()
        if pd.notna(max_len):
            column_len = max(column_len, max_len)
        worksheet.set_column(i, i, column_len + 2)


def write_projection_balances_with_links(writer, df, nav_links, nav_col):
    """Writes the Projection Balances DataFrame to a sheet with a hyperlink for 'Ideal Budget'."""
    sheet_name = 'Projection Balances'
    workbook = writer.book
    worksheet = workbook.add_worksheet(sheet_name)
    writer.sheets[sheet_name] = worksheet

    # Add formats
    header_format = workbook.add_format({'bold': True, 'bottom': 1})
    num_format = workbook.add_format({'num_format': '#,###.00'})
    url_format = workbook.add_format({'color': 'blue', 'underline': 1})
    date_format = workbook.add_format({'num_format': 'mm/dd/yyyy'})

    # Write header
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_format)

    # Write data rows
    eoy_col_idx = df.columns.get_loc('End of Year')
    for row_num, row_data in enumerate(df.itertuples(index=False), 1):
        for col_num, cell_data in enumerate(row_data):
            if col_num == eoy_col_idx and cell_data == 'Ideal Budget':
                url = "internal:'Ideal Projection'!A1"
                worksheet.write_url(row_num, col_num, url, cell_format=url_format, string=cell_data)
            else:
                if isinstance(cell_data, datetime.date):
                    worksheet.write_datetime(row_num, col_num, cell_data, date_format)
                elif isinstance(cell_data, (int, float)):
                    if pd.isna(cell_data):
                        worksheet.write_blank(row_num, col_num, None)
                    else:
                        worksheet.write_number(row_num, col_num, cell_data, num_format)
                else:
                    worksheet.write(row_num, col_num, cell_data)

    # Add navigation links
    for i, link_sheet in enumerate(nav_links, start=1):
        cell = f'{nav_col}{i}'
        url = f"internal:'{link_sheet}'!A1"
        worksheet.write_url(cell, url, cell_format=url_format, string=link_sheet)

    # Auto-adjust column widths
    for i, col in enumerate(df.columns):
        column_len = len(col)
        max_len = df[col].astype(str).map(len).max()
        if pd.notna(max_len):
            column_len = max(column_len, max_len)
        worksheet.set_column(i, i, column_len + 2)


def write_budget(budget_dict, projection_dict, initial_sheets, monthly_sums_dict, xls_name, category_types,
                 ideal_budget, ideal_monthly_sums_dict, diff_outs, disc_summary, yearly_summary, remaining_expenses, this_year):
    """Write the updated budget to an Excel file"""
    writer = pd.ExcelWriter(xls_name, engine='xlsxwriter')
    nav_links = ['Diffs', 'Q Summary', 'Y Summary', 'Yearly Remaining', 'Expenses', 'Categories', 'Projection Balances']

    # Write out the diffs and the summary of quarters
    d_out = {'Category': list(diff_outs.keys()), 'Amount': [diff_outs[x] for x in diff_outs.keys()]}
    df_out = pd.DataFrame(d_out)
    write_summary_sheet_with_links(writer, df_out, 'Diffs', nav_links=nav_links, nav_col='E')
    
    df_disc = pd.DataFrame(disc_summary)
    df_disc.sort_values('Category', inplace=True)
    write_summary_sheet_with_links(writer, df_disc, 'Q Summary', nav_links=nav_links, nav_col='G')

    df_yearly = pd.DataFrame(yearly_summary)
    df_yearly.sort_values('Category', inplace=True)
    write_summary_sheet_with_links(writer, df_yearly, 'Y Summary', nav_links=nav_links, nav_col='G')

    # Create the Yearly Remaining sheet with 5-year projection
    # Update the year columns to be programmatic (5 years ahead)
    current_year = this_year
    years_ahead = 5
    remaining_expenses_with_programmatic_years = {'Category': remaining_expenses['Category']}
    
    for i in range(years_ahead):
        year = current_year + i
        year_key = str(year)
        if year_key in remaining_expenses:
            remaining_expenses_with_programmatic_years[str(year)] = remaining_expenses[year_key]
        else:
            # If the year doesn't exist in the data, fill with zeros
            remaining_expenses_with_programmatic_years[str(year)] = [0.0] * len(remaining_expenses['Category'])
    
    df_remaining = pd.DataFrame(remaining_expenses_with_programmatic_years)
    df_remaining.sort_values('Category', inplace=True)
    write_summary_sheet_with_links(writer, df_remaining, 'Yearly Remaining', nav_links=nav_links, nav_col='H')

    # Recreate the initial sheets
    for dict_name, dict_initial in initial_sheets.items():
        if dict_name == 'Expenses':
            df_expenses = pd.DataFrame(dict_initial)
            write_summary_sheet_with_links(writer, df_expenses, 'Expenses', nav_links=nav_links, nav_col='F')
        elif dict_name == 'Categories':
            # Make sure all columns are the same length for dataframe creation
            max_len = max(len(v) for v in dict_initial.values())
            for k, v in dict_initial.items():
                if len(v) < max_len:
                    dict_initial[k].extend([''] * (max_len - len(v)))
            df_categories = pd.DataFrame(dict_initial)
            category_sheet_list = list(budget_dict.keys())
            write_sheet_with_all_category_links(writer, df_categories, 'Categories', category_sheet_list, nav_links=nav_links, nav_col='G')
        elif dict_name == 'Balances':
            df_balances = pd.DataFrame(dict_initial)
            write_sheet_with_nav_panel(writer, df_balances, 'Balances', nav_links, 'E')
        else:
            df_initial = pd.DataFrame(dict_initial)
            df_initial.to_excel(writer, sheet_name=dict_name, index=False, na_rep='')
            make_xls_pretty(writer, df_initial, dict_name)

    # Get key date balances
    # this_year = datetime.date.today().year
    end_of_years = [datetime.date(this_year + i, 12, 31) for i in range(0, 6)]
    last_amount_in_years = []
    for end_of_year in end_of_years:
        i_locs = [i for i, x in enumerate(projection_dict['Date']) if x == end_of_year]
        last_amount_in_years.append(projection_dict['Balance'][i_locs[-1]])

    # Make the projection sheet
    print(f'Writing new budget xls: {xls_name}')
    dates_to_str(projection_dict)
    df_projection = pd.DataFrame(projection_dict)
    df_projection.to_excel(writer, sheet_name='Projection', index=False, na_rep='')
    make_xls_pretty(writer, df_projection, 'Projection')

    # Make the ideal projection sheet
    dates_to_str(ideal_budget)
    df_ideal = pd.DataFrame(ideal_budget)
    df_ideal.to_excel(writer, sheet_name='Ideal Projection', index=False, na_rep='')
    make_xls_pretty(writer, df_ideal, 'Ideal Projection')

    projection_balances = {'End of Year': end_of_years, 'Balance': last_amount_in_years}
    projection_balances['End of Year'].append('Ideal Budget')
    projection_balances['Balance'].append(ideal_budget['Balance'][-1])
    df_projection_balances = pd.DataFrame(projection_balances)
    write_projection_balances_with_links(writer, df_projection_balances, nav_links, 'E')

    # Set the order of output
    categories = list(budget_dict.keys())
    big_rocks = ['Paycheck', 'Charity', 'Mortgage', 'Taxes']
    yearly_categories = remove_list_blanks_nonzero(category_types['Yearly'])
    yearly_categories.sort()
    yearly_categories = [x for x in yearly_categories if 'Charity' != x]
    loan_categories = remove_list_blanks_nonzero(category_types['Loan'])
    loan_categories.sort()
    q_categories = remove_list_blanks_nonzero(category_types['Quarterly'])
    q_categories.sort()
    m_categories = remove_list_blanks_nonzero(category_types['Monthly'])
    m_categories.sort()
    preferred_order = ['Interest'] + loan_categories + yearly_categories + q_categories + m_categories
    new_top_categories = big_rocks + preferred_order
    other_categories = [x for x in categories if x not in new_top_categories]
    other_categories.sort()
    categories_organized = new_top_categories + other_categories

    # Create the monthly sums sheet
    final_monthly_dict = finalize_monthly_dict(categories_organized, monthly_sums_dict)

    df_monthly_sums = pd.DataFrame(final_monthly_dict)
    df_monthly_sums.to_excel(writer, sheet_name='Monthly', index=False, na_rep='')
    make_xls_pretty(writer, df_monthly_sums, 'Monthly', all=True)

    # Create the ideal monthly sums sheet
    final_ideal_monthly_dict = finalize_monthly_dict(categories_organized, ideal_monthly_sums_dict)

    df_ideal_monthly_sums = pd.DataFrame(final_ideal_monthly_dict)
    df_ideal_monthly_sums.to_excel(writer, sheet_name='Ideal Monthly', index=False, na_rep='')
    make_xls_pretty(writer, df_ideal_monthly_sums, 'Ideal Monthly', all=True)

    # Loop over each category and create the spreadsheet
    for category in categories_organized:
        # print(category)
        category_budget_raw = budget_dict[category]
        category_budget = make_dict_list_same_len(category_budget_raw)
        dates_to_str(category_budget)
        df = pd.DataFrame(category_budget)

        # If Month in df columns then add empty column at position 5
        if 'End of Month' in df.columns and category not in category_types['Monthly'] and ' ' not in df.columns:
            if category in category_types['Loan']:
                df.insert(loc=5, column=' ', value=['' for i in range(df.shape[0])])
            else:
                df.insert(loc=6, column=' ', value=['' for i in range(df.shape[0])])

        sheet_created = False
        if 'Actual' in df.columns and 'Planned' in df.columns:
            p_sum = sum([abs(x) for x in df.Actual if x != '']) + sum([abs(x) for x in df.Planned if x != ''])
            if abs(p_sum) > 0.0:
                df.to_excel(writer, sheet_name=category, index=False, na_rep='')
                make_xls_pretty(writer, df, category)
                sheet_created = True
            else:
                print(f'This category budget is empty: {category}')
        else:
            df.to_excel(writer, sheet_name=category, index=False, na_rep='')
            make_xls_pretty(writer, df, category)
            sheet_created = True

        if sheet_created:
            # Add navigation links to the sheet
            worksheet = writer.sheets[category]
            url_format = writer.book.add_format({'color': 'blue', 'underline': 1})
            
            for i, link_sheet in enumerate(nav_links, start=1):
                cell = f'O{i}'
                url = f"internal:'{link_sheet}'!A1"
                worksheet.write_url(cell, url, cell_format=url_format, string=link_sheet)

    writer.close()


def remove_specials(my_str):
    return my_str.replace('Loan - ', '').replace('M ', '',).replace('Y ', '').replace('Q ', '')


def finalize_monthly_dict(categories_organized, monthly_sums_dict):
    """Function to add sum row and column"""

    monthly_headers = [
        f'{datetime.date(datetime.date.today().year, i + 1, 1).strftime("%B")} {datetime.date.today().year}'
        for i in range(0, 12)]
    monthly_dict = {'Categories': categories_organized}
    categories_update = [x for x in categories_organized
                         if x in monthly_sums_dict.keys()]
    for i, monthly_header in enumerate(monthly_headers):
        monthly_dict[monthly_header] = [0.0]*len(categories_update)
        for c, category in enumerate(categories_update):
            for this_line in monthly_sums_dict[category]:
                if i + 1 == this_line[0].month:
                    monthly_dict[monthly_header][c] = this_line[1]
                    break
    monthly_dict['Categories'] = categories_update
    monthly_dict['Categories'].append('Monthly Total')
    monthly_sums = [sum(monthly_dict[x]) for x in monthly_dict.keys() if x != 'Categories']
    c = 0
    new_monthly_dict = monthly_dict.copy()
    for m_key, m_list in monthly_dict.items():
        if m_key != 'Categories':
            new_monthly_dict[m_key].append(monthly_sums[c])
            c += 1
    final_monthly_dict = new_monthly_dict.copy()
    final_monthly_dict['Yearly'] = [0.0]*len(categories_update)
    for c, category in enumerate(categories_update):
        sums = 0.0
        for m, month in enumerate(list(new_monthly_dict.keys())[1:]):
            sums += final_monthly_dict[month][c]
        final_monthly_dict['Yearly'][c] = sums

    return final_monthly_dict
