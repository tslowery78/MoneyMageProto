from get_sums import get_monthly_sums
from budget_functions import parse_loan_budget, parse_quarterly_budget, parse_monthly_budget, parse_default_budget
from dateutil.relativedelta import relativedelta


def parse_budget(category, category_budget, transactions, expenses, category_types, this_year):

    # Rename all # descriptions
    if 'Desc.' in category_budget.keys():
        category_budget['Desc.'] = [x.split()[0] + f' {category}' if '#' in x else x
                                    for x in category_budget['Desc.']]
        category_budget['Desc.'] = [' '.join(list(dict.fromkeys(x.split()))) for x in category_budget['Desc.']]

    # Determine category monthly totals for all transactions
    if transactions:
        actual_monthly_sums = get_monthly_sums(category, transactions['Date'],
                                               transactions['Amount'], transactions['Category'])
    else:
        actual_monthly_sums = []

    # Determine the type of budget for this category and parse
    if category in category_types['Loan']:
        category_budget, year_projection, multi_year_projection = \
            parse_loan_budget(category, category_budget, actual_monthly_sums, this_year)

    elif category in category_types['Quarterly']:
        category_budget, year_projection, multi_year_projection = \
            parse_quarterly_budget(category, category_budget, transactions, this_year)

    elif category in category_types['Monthly']:
        category_budget, year_projection, multi_year_projection = \
            parse_monthly_budget(category, category_budget, actual_monthly_sums)

    else:  # default
        category_budget, year_projection, multi_year_projection = \
            parse_default_budget(category, category_budget, actual_monthly_sums, expenses, category_types, this_year)

    # Extend the multi-year projection out to 5 years
    forecast = []
    for i in range(0, 5):
        forecast.append(
            [[x[0] + relativedelta(years=i + 1),
              f'Forecast: {category} for {x[0].strftime("%B")} {x[0].year + i + 1}',
              x[1], category, 0.0, ''] for x in multi_year_projection if abs(x[1]) > 0.0]
        )

    return category_budget, year_projection, forecast
