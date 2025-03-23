from datetime import datetime, date
from utilities import remove_list_blanks, end_of_month, in_this_month, range_eom_dates
import pandas as pd


def get_monthly_sums(category, dates, amounts, transactions_categories):
    """Function to get a list of the month sums per month"""

    # Get the monthly series in this time series
    dates_sorted = dates.copy()
    try:
        dates_sorted.sort()
    except TypeError:
        print('pass')
        # dates_sorted = [date if pd.notna(date) else None for date in dates_sorted]
        # dates_sorted.sort(key=lambda x: (x is None, x))

    if not dates:
        return []
    try:
        monthly_dates = range_eom_dates(dates_sorted[0], dates_sorted[-1])
    except UnboundLocalError:
        print('pass')

    # Find this year's monthly sums
    amounts_in = remove_list_blanks(amounts)
    monthly_sums = [0.0]*len(monthly_dates)
    for d, transaction_date in enumerate(dates):
        if category and transactions_categories:
            if category != transactions_categories[d]:
                continue
        i_month = [i for i, x in enumerate(monthly_dates) if in_this_month(transaction_date, x)]
        if i_month:
            monthly_sums[i_month[0]] += amounts_in[d]

    return [(monthly_dates[i], x) for i, x in enumerate(monthly_sums)]


def get_quarterly_sums(category, dates, amounts, transactions_categories, expense):
    """Function to get a list of the month sums per month"""

    # Find this year's quarterly sums
    quarterly_sums = [0.0]*4
    quarterly_months = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]
    for d, transaction_date in enumerate(dates):
        if category and transactions_categories:
            if category != transactions_categories[d]:
                continue
        i_quarter = [i for i, x in enumerate(quarterly_months) if transaction_date.month in x][0]
        quarterly_sums[i_quarter] += amounts[d]

    this_quarter = [i for i, x in enumerate(quarterly_months) if datetime.today().month in x][0]
    spent = [(i, x) for i, x in enumerate(quarterly_sums)]
    remaining = []
    for i in range(0, 4):
        if i == this_quarter:
            if spent[i][1] < expense[i]:
                remaining.append((i, 0.0))
            else:
                remaining.append((i, expense[i] - spent[i][1]))
        elif i < this_quarter:
            remaining.append((i, 0.0))
        else:
            remaining.append((i, expense[i]))


    # # Find the current quarter
    # this_quarter = [i for i, x in enumerate(quarterly_months) if datetime.today().month in x][0]
    # quarters_remaining = 4 - this_quarter - 1
    # remaining = []
    # pile = float(sum(expense))
    # for q in range(0, 4):
    #     if q < this_quarter:
    #         remaining.append((q, 0.0))
    #         pile -= quarterly_sums[q]
    #         if pile > 0.0:
    #             pile = 0.0
    #     elif q == this_quarter:
    #         diff = pile/(quarters_remaining + 1) - quarterly_sums[q]
    #         if diff > 0.0:
    #             pile -= quarterly_sums[q]
    #             remaining.append((q, 0.0))
    #         else:
    #             remaining.append((q, diff))
    #     else:
    #         left = pile/(quarters_remaining + 1)
    #         remaining.append((q, left))
    #
    # spent = [(i, x) for i, x in enumerate(quarterly_sums)]

    return spent, remaining


