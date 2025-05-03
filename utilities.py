from datetime import timedelta, date, datetime
from difflib import SequenceMatcher


def remove_list_blanks_nonzero(my_list):
    return [x for x in my_list if x != '']


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def cat_lists(*arguments):
    cat_list = []
    for mylist in arguments:
        cat_list.extend(mylist)
    return cat_list


def end_of_month(my_date):
    """Get the end of the current month's date"""
    return date(my_date.year + int(my_date.month / 12), my_date.month % 12 + 1, 1) - timedelta(days=1)


def remove_list_blanks(my_list):
    """Turn blanks into zeros in a list"""
    out_list = []
    for item in my_list:
        if isinstance(item, float):
            out_list.append(item)
        elif isinstance(item, int):
            out_list.append(float(item))
        else:
            out_list.append(0.0)

    return out_list


def in_this_month(my_date, this_date):
    """Determine if my date is in the same month as this date"""
    if my_date.year == this_date.year and my_date.month == this_date.month:
        return True
    else:
        return False


def dates_to_str(my_dict):
    """Convert the date key values into strings for output"""

    for key, key_list in my_dict.items():
        if key == 'Date' or key == 'Month' or key == 'End of Year':
            dates = my_dict[key]
            if not dates:
                continue
            if isinstance(dates[0], int):
                continue
            my_dict[key] = ['' if x == '' else x.strftime('%m/%d/%Y') for x in dates]


def make_dict_list_same_len(my_dict):
    """Function to make the lists of a dict the same length by adding empty cells"""

    # Determine the longest column length
    longest_len = max([len(my_dict[x]) for x in list(my_dict.keys())])

    # For each list in dict, lengthen the list to the longest length
    new_dict = {}
    for key, dict_list in my_dict.items():
        new_list = ['']*longest_len
        new_list[0:len(dict_list)] = dict_list
        new_dict[key] = new_list

    return new_dict


def remove_empty_rows(my_dict, key_base):
    """Function to remove the empty rows, based on first column"""
    out_dict = {}
    max_length = len([x for x in my_dict[key_base] if x != ''])
    for key, my_list in my_dict.items():
        out_dict[key] = my_list[0:max_length]
    return out_dict


def remove_tuple_zeros(my_list):
    """Removes zero valued tuple pairs from a list"""
    return [x for x in my_list if x[1] != 0.0]


def range_eom_dates(first_date, last_date):
    start_month = first_date.month
    try:
        end_months = (last_date.year - first_date.year) * 12 + last_date.month + 1
    except AttributeError:
        print('pass')
    r_out = []
    try:
        r_out = [end_of_month(datetime(year=yr, month=mn, day=1)) for (yr, mn) in
                 ((int((m - 1) / 12) + first_date.year, (m - 1) % 12 + 1) for m in range(start_month, end_months))]
    except TypeError:
        print('pass')
    return r_out
