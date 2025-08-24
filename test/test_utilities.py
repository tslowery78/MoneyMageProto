import datetime

import pytest

from utilities import (
    end_of_month,
    remove_list_blanks,
    make_dict_list_same_len,
    remove_empty_rows,
    range_eom_dates,
    similar,
    dates_to_str,
    remove_list_blanks_nonzero,
    remove_tuple_zeros,
)


def test_end_of_month_basic_and_leap_year():
    assert end_of_month(datetime.date(2024, 1, 15)) == datetime.date(2024, 1, 31)
    assert end_of_month(datetime.date(2024, 2, 10)) == datetime.date(2024, 2, 29)


def test_remove_list_blanks_converts_non_numbers_to_zero_and_ints_to_float():
    data = [1, 2.5, "", "foo", None]
    assert remove_list_blanks(data) == [1.0, 2.5, 0.0, 0.0, 0.0]


def test_make_dict_list_same_len_extends_shorter_lists():
    input_dict = {"A": [1, 2], "B": [3]}
    out = make_dict_list_same_len(input_dict)
    assert len(out["A"]) == len(out["B"]) == 2
    assert out["B"] == [3, ""]


def test_remove_empty_rows_uses_base_key_non_empty_count():
    data = {"Base": ["x", "", ""], "Other": [10, 20, 30]}
    out = remove_empty_rows(data, "Base")
    assert out == {"Base": ["x"], "Other": [10]}


def test_range_eom_dates_includes_each_month_end_inclusive():
    dates = range_eom_dates(datetime.date(2024, 1, 15), datetime.date(2024, 3, 2))
    assert dates == [
        datetime.date(2024, 1, 31),
        datetime.date(2024, 2, 29),
        datetime.date(2024, 3, 31),
    ]


def test_similar_string_matches():
    assert similar("abc", "abc") == pytest.approx(1.0)
    assert similar("abc", "abd") < 1.0


def test_dates_to_str_formats_date_columns():
    d = {"Date": [datetime.date(2024, 1, 2), ""], "Other": [1, 2]}
    dates_to_str(d)
    assert d["Date"] == ["01/02/2024", ""]


def test_remove_list_blanks_nonzero_filters_empty_strings():
    assert remove_list_blanks_nonzero(["", "a", "", "b"]) == ["a", "b"]


def test_remove_tuple_zeros_filters_zero_amount_pairs():
    assert remove_tuple_zeros([("a", 0.0), ("b", 1.0), ("c", 0.0)]) == [("b", 1.0)]


