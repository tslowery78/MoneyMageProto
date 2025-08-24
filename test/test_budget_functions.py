import datetime

from budget_functions import (
    remove_budget_integers,
    get_reconciled_budget,
    get_forward_budget,
    make_monthly_table,
    get_year_projection,
)


def test_remove_budget_integers_coerces_values_to_float_and_blanks_to_zero():
    category_budget = {"Amount": [1, "2", None, "x", 3.5]}
    fixed = remove_budget_integers(category_budget)
    assert fixed["Amount"] == [1.0, 2.0, 0.0, 0.0, 3.5]


def test_get_reconciled_and_forward_budget_indexing():
    budget = {
        "R": ["", "X", "", "R"],
        "Date": [1, 2, 3, 4],
        "This Year": [10.0, 20.0, 30.0, 40.0],
    }
    reconciled = get_reconciled_budget(budget)
    assert reconciled["R"] == ["X", "R"]
    assert reconciled["This Year"] == [20.0, 40.0]

    forward = get_forward_budget(budget)
    assert forward["R"] == ["", ""]
    assert forward["Date"] == [1, 3]


def test_make_monthly_table_populates_expected_fields():
    this_year = 2024
    # Actuals for Jan only
    actual_monthly_sums = [
        (datetime.date(2024, 1, 31), 100.0),
    ]
    # Planned for Jan and Feb
    all_planned_monthly_sums = [
        (datetime.date(2024, 1, 31), 50.0),
        (datetime.date(2024, 2, 29), 50.0),
    ]
    reconciled_monthly_sums = [
        (datetime.date(2024, 1, 31), 0.0),
        (datetime.date(2024, 2, 29), 0.0),
    ]
    category_budget = {}

    out = make_monthly_table(
        actual_monthly_sums,
        all_planned_monthly_sums,
        reconciled_monthly_sums,
        category_budget,
        this_year,
    )

    # Ensure keys exist
    assert set(["End of Month", "Actual", "Reconciled", "Difference", "Planned"]) <= set(out.keys())
    # There should be at least two months from the inputs (Jan, Feb)
    assert datetime.date(2024, 1, 31) in out["End of Month"]
    assert datetime.date(2024, 2, 29) in out["End of Month"]
    # Check expected values for Jan and Feb
    jan_index = out["End of Month"].index(datetime.date(2024, 1, 31))
    feb_index = out["End of Month"].index(datetime.date(2024, 2, 29))
    assert out["Actual"][jan_index] == 100.0
    assert out["Actual"][feb_index] == 0.0
    assert out["Planned"][jan_index] == 50.0
    assert out["Planned"][feb_index] == 50.0
    assert out["Difference"][jan_index] == 100.0  # reconciled 0.0


def test_get_year_projection_combines_actuals_and_future_non_zero():
    category = "TestCat"
    forward_category_budget = {
        "Date": [datetime.date(2024, 3, 31), datetime.date(2024, 4, 30)],
        "Desc.": ["Planned A", "Planned B"],
        "This Year": [0.0, 25.0],
        "Note": ["n1", "n2"],
    }
    actual_monthly_sums = [
        (datetime.date(2024, 1, 31), 100.0),
        (datetime.date(2024, 2, 29), 0.0),
    ]

    rows = get_year_projection(category, forward_category_budget, actual_monthly_sums)

    # One actual row with non-zero, plus one forward row with non-zero
    assert len(rows) == 2
    # Check categories and descriptions are propagated
    assert rows[0][3] == category
    assert any("Planned B" in r[1] for r in rows)


