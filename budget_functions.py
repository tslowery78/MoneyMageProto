import datetime
from datetime import date
from get_sums import get_monthly_sums, get_quarterly_sums
from utilities import end_of_month, remove_list_blanks, make_dict_list_same_len, range_eom_dates


def remove_budget_integers(category_budget):
    """turn integers into floats for each amount/payment/ect."""
    a_types = ['Amount', 'Payment', 'Planned', 'This Year', 'Next Year']
    fixed_category_budget = category_budget.copy()
    for a_type in a_types:
        if a_type in category_budget.keys():
            # Ensure all values are numeric, replacing blanks/non-numeric with 0.0
            new_values = []
            for val in category_budget[a_type]:
                try:
                    # Attempt to convert to float. Handles int, float, and string representations of numbers.
                    new_values.append(float(val))
                except (ValueError, TypeError):
                    # If conversion fails, it's not a number or it's None/etc. Replace with 0.0
                    new_values.append(0.0)
            fixed_category_budget[a_type] = new_values
    return fixed_category_budget


def get_reconciled_budget(budget):
    """Function to get the reconciled budget plan"""
    i_reconciled = [i for i, x in enumerate(budget['R']) if x != '']
    reconciled = {}
    for key, key_list in budget.items():
        reconciled[key] = [key_list[i] for i in i_reconciled]
    return reconciled


def get_forward_budget(budget):
    """Function get the forward non-reconciled budget plan"""
    if not budget:
        return budget
    if not budget['R']:
        return budget
    i_not_reconciled = [i for i, x in enumerate(budget['R']) if x == '']
    forward = {}
    for key, key_list in budget.items():
        forward[key] = [key_list[i] for i in i_not_reconciled]
    return forward


def make_monthly_table(actual_monthly_sums, all_planned_monthly_sums, reconciled_monthly_sums, category_budget, 
                       this_year):
    """Update the category's budget with the actual monthly sums in a table on the right side"""

    if not all_planned_monthly_sums:
        this_years_dates = range_eom_dates(date(this_year, 1, 1),
                                           date(this_year, 12, 31))
        all_planned_monthly_sums = [(x, 0.0) for x in this_years_dates]

    if not actual_monthly_sums:
        first_date = all_planned_monthly_sums[0][0]
        last_date = all_planned_monthly_sums[-1][0]
    else:
        first_date = actual_monthly_sums[0][0]
        if actual_monthly_sums[-1] > all_planned_monthly_sums[-1]:
            last_date = actual_monthly_sums[-1][0]
        else:
            last_date = all_planned_monthly_sums[-1][0]
    all_months = range_eom_dates(first_date, last_date)
    category_budget['End of Month'] = all_months
    if actual_monthly_sums:
        category_budget['Actual'] = [[y[1] for y in actual_monthly_sums if y[0] == x][0]
                                     if [y[1] for y in actual_monthly_sums if y[0] == x] else 0.0
                                     for i, x in enumerate(all_months)]
    else:
        category_budget['Actual'] = [0.0 for i, x in enumerate(all_months)]
    category_budget['Reconciled'] = [[y[1] for y in reconciled_monthly_sums if y[0] == x][0]
                                     if [y[1] for y in reconciled_monthly_sums if y[0] == x] else 0.0
                                     for i, x in enumerate(all_months)]
    category_budget['Difference'] = [x - category_budget['Reconciled'][i] for i, x in
                                     enumerate(category_budget['Actual'])]
    category_budget['Planned'] = [[y[1] for y in all_planned_monthly_sums if y[0] == x][0]
                                  if [y[1] for y in all_planned_monthly_sums if y[0] == x] else 0.0
                                  for i, x in enumerate(all_months)]
    category_budget = make_dict_list_same_len(category_budget)

    return category_budget


def get_year_projection(category, forward_category_budget, actual_monthly_sums):
    """Get the year's projection using actual monthly totals and planned transactions"""

    # Create this year's projection series and future year's estimate
    this_key = 'This Year'
    if 'Payment' in forward_category_budget.keys():
        this_key = 'Payment'
    future_transactions = [[x, f'{forward_category_budget["Desc."][i]} in {x.strftime("%B")} {x.year}',
                            forward_category_budget[this_key][i], category, 0.0, forward_category_budget['Note'][i]]
                           for i, x in enumerate(forward_category_budget['Date'])]
    future_transactions = [x for x in future_transactions if x[2] != 0.0]
    actual_monthly_totals = []
    if actual_monthly_sums:
        actual_monthly_totals = [[x[0], f'{category} total for {x[0].strftime("%B")} {x[0].year}', x[1], category, 0.0, '']
                                 for x in actual_monthly_sums]
        actual_monthly_totals = [x for x in actual_monthly_totals if x[2] != 0.0]

    return actual_monthly_totals + future_transactions


def parse_loan_budget(category, category_budget, actual_monthly_sums, this_year):
    """Parses a loan type budget"""

    # Check the budget for needed keys
    if 'Payment' not in category_budget.keys():
        raise Exception(f'Payment is not in {category}')

    # Remove reconciled transactions from the category budget
    forward_category_budget = get_forward_budget(category_budget)
    reconciled_category_budget = get_reconciled_budget(category_budget)

    # Get the planned monthly totals
    all_planned_monthly_sums = get_monthly_sums(None, category_budget['Date'], category_budget['Payment'], None)
    reconciled_monthly_sums = get_monthly_sums(None, reconciled_category_budget['Date'],
                                               reconciled_category_budget['Payment'], None)

    # Update the category's budget with the actual monthly sums in a table on the right side
    category_budget = make_monthly_table(actual_monthly_sums, all_planned_monthly_sums,
                                         reconciled_monthly_sums, category_budget, this_year)

    # Create this year's projection series and future year's estimate
    year_projection = get_year_projection(category, forward_category_budget, actual_monthly_sums)

    return category_budget, year_projection, []


def parse_quarterly_budget(category, category_budget, transactions, this_year):
    """Parses a quarterly type budget"""

    # Get the category's quarterly sums
    if transactions:
        quarterly_spent, quarterly_remaining = get_quarterly_sums(
            category, transactions['Date'], transactions['Amount'], transactions['Category'], category_budget['This Year'])
    else:
        quarterly_spent, quarterly_remaining = get_quarterly_sums(
            category, [], [], [], category_budget['This Year'])
    category_budget['Spent'] = [x[1] for x in quarterly_spent]
    category_budget['Remaining'] = [x[1] for x in quarterly_remaining]

    # Get the planned quarterly sums
    quarter_dates = [date(this_year, 3, 31), date(this_year, 6, 30), date(this_year, 9, 30),
                     date(this_year, 12, 31)]
    multi_year_projection = [(quarter_dates[i], category_budget['Next Year'][i]) for i in range(0, 4)]
    future_transactions = [[x, f'Planned {category} for Quarter {i + 1} in {x.strftime("%B")} {x.year}',
                            quarterly_remaining[i][1], category, 0.0, '']
                           for i, x in enumerate(quarter_dates)]
    future_transactions = [x for x in future_transactions if x[2] != 0.0]
    actual_monthly_totals = [[x, f'{category} total for Quarter {i + 1} {x.year}', quarterly_spent[i][1],
                              category, 0.0, ''] for i, x in enumerate(quarter_dates)]
    actual_monthly_totals = [x for x in actual_monthly_totals if x[2] != 0.0]

    year_projection = actual_monthly_totals + future_transactions

    return category_budget, year_projection, multi_year_projection


def parse_monthly_budget(category, category_budget, actual_monthly_sums):
    """Parses a monthly type budget"""

    # Get the yearly expense
    this_month = date.today().month
    this_year = date.today().year
    remaining = [0.0] * 12
    value = 0.0
    for i in range(0, 12):
        if i + 1 < this_month:
            value = 0.0
        if i + 1 == this_month:
            if i < len(actual_monthly_sums):
                value = category_budget['Planned'][i] - actual_monthly_sums[i][1]
            else:
                value = category_budget['Planned'][i]
            if value > 0.0:
                value = 0.0
        if i + 1 > this_month:
            value = category_budget['Planned'][i]
        remaining[i] = value
    category_budget['Spent - Yearly Planned'] = [x[1] - category_budget['Planned'][i]
                                                 for i, x in enumerate(actual_monthly_sums)]
    category_budget['Spent - Yearly Planned'] = [category_budget['Spent - Yearly Planned'][i]
                                                 if i < len(category_budget['Spent - Yearly Planned']) else
                                                 0.0 for i in range(0, 12)]
    category_budget['Remaining'] = remaining
    category_budget['Spent'] = [x[1] for x in actual_monthly_sums] + [0.0] * (12 - len(actual_monthly_sums))
    monthly_dates = [end_of_month(datetime.date(this_year, i + 1, 1)) for i in range(0, 12)]
    future_transactions = [[x, f'Planned {category} for {x.strftime("%B")} {x.year}',
                            remaining[i], category, 0.0, '']
                           for i, x in enumerate(monthly_dates)]
    future_transactions = [x for x in future_transactions if x[2] != 0.0]
    actual_monthly_totals = [[x, f'{category} total for Month {i + 1} {x.year}', category_budget['Spent'][i],
                              category, 0.0, ''] for i, x in enumerate(monthly_dates)]
    actual_monthly_totals = [x for x in actual_monthly_totals if x[2] != 0.0]

    year_projection = actual_monthly_totals + future_transactions

    multi_year_projection = [(end_of_month(date(this_year, i + 1, 1)), category_budget['Next Year'][i])
                             for i in range(0, 12)]

    return category_budget, year_projection, multi_year_projection


def parse_yearly_expense(category, category_budget, actual_monthly_sums, expenses):
    """Parses a default yearly expense"""

    # Remove Existing Yearly row
    i_yearly = [i for i, x in enumerate(category_budget['Desc.']) if x == 'Yearly']
    new_category_budget = category_budget.copy()
    if i_yearly:
        for key, key_list in category_budget.items():
            new_category_budget[key] = \
                [category_budget[key][i] for i, x in enumerate(category_budget['Desc.']) if x != 'Yearly']
    category_budget = new_category_budget
    forward_budget = get_forward_budget(category_budget)

    try:
        i_expense = [i for i, x in enumerate(expenses['Category']) if x == category][0]
    except IndexError:
        raise Exception(f'Category {category} not in Expenses sheet')
    this_years_plan = expenses['This Year'][i_expense]
    next_years_plan = expenses['Next Year'][i_expense]
    next_years_plan_to_date = sum(remove_list_blanks(category_budget['Next Year']))
    this_years_leftover = this_years_plan - (sum([x[1] for x in actual_monthly_sums]) +
                                             sum(forward_budget['This Year']))
    if this_years_leftover > 0.0:
        this_years_leftover = 0.0
    next_years_leftover = next_years_plan - next_years_plan_to_date
    if next_years_leftover > 0.0:
        next_years_leftover = 0.0
    category_budget['This Year'].append(this_years_leftover)
    category_budget['Next Year'].append(next_years_leftover)
    category_budget['Date'].append(date(date.today().year, 12, 31))
    category_budget['Desc.'].append('Yearly')
    category_budget = make_dict_list_same_len(category_budget)

    return category_budget


def parse_default_budget(category, category_budget, actual_monthly_sums, expenses, category_types, this_year):
    """Parses a default type budget"""

    # Check for needed keys
    if 'Date' not in category_budget.keys():
        if not category_budget:
            category_budget = {'Date': [], 'Desc.': [], 'This Year': [], 'R': [],
                               'Next Year': [], 'Note': []}
        else:
            raise Exception(f'Date not in {category}')

    # If this is a yearly expense, set the "Yearly" expense row minus the actual spending for the category
    if category in category_types['Yearly']:
        category_budget = parse_yearly_expense(category, category_budget, actual_monthly_sums, expenses)

        # Calculate total spent and remaining
        total_planned = 0
        try:
            i_expense = [i for i, x in enumerate(expenses['Category']) if x == category][0]
            total_planned = expenses['This Year'][i_expense]
        except IndexError:
            pass  # Category might not be in expenses, handled in parse_yearly_expense

        total_spent = sum(x[1] for x in actual_monthly_sums)
        remaining = total_planned - total_spent
        
        category_budget['Remaining'] = [remaining]

        # Ensure all lists have the same length before proceeding
        category_budget = make_dict_list_same_len(category_budget)

    # Remove reconciled transactions from the category budget
    forward_category_budget = get_forward_budget(category_budget)
    reconciled_category_budget = get_reconciled_budget(category_budget)

    # Get the planned and future monthly totals
    try:
        all_planned_monthly_sums = get_monthly_sums(None, category_budget['Date'], category_budget['This Year'], None)
    except KeyError:
        pass
    reconciled_monthly_sums = get_monthly_sums(None, reconciled_category_budget['Date'],
                                               reconciled_category_budget['This Year'], None)
    multi_year_projection = get_monthly_sums(None, category_budget['Date'], category_budget['Next Year'], None)

    # Update the category's budget with the actual monthly sums in a table on the right side
    category_budget = make_monthly_table(actual_monthly_sums, all_planned_monthly_sums,
                                         reconciled_monthly_sums, category_budget, this_year)

    # Create this year's projection series and future year's estimate
    year_projection = get_year_projection(category, forward_category_budget, actual_monthly_sums)

    return category_budget, year_projection, multi_year_projection
