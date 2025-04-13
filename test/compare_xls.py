import pandas as pd
import os
import sys

def compare_excel_files(filename):
    """
    Compares each sheet in two Excel files and reports only the differences.
    One file is in the directory where the script is located, and the other
    is in the directory above. The files are assumed to have the same name.

    Args:
        filename (str): The name of the Excel file (including extension, e.g., "data.xlsx").

    Returns:
        dict: A dictionary where keys are sheet names and values are booleans
              indicating whether the sheets are identical (True) or not (False).
              Returns None if an error occurs. Prints detailed comparison
              information *only for differing sheets* to the console.
    """
    script_directory = os.path.dirname(os.path.abspath(__file__))
    parent_directory = os.path.dirname(script_directory)
    file1_path = os.path.join(script_directory, filename)
    file2_path = os.path.join(parent_directory, filename)

    print(f"Comparing files:\n  {file1_path}\n  {file2_path}")

    try:
        excel_file1 = pd.ExcelFile(file1_path)
        excel_file2 = pd.ExcelFile(file2_path)
    except FileNotFoundError:
        print(f"Error: One or both files not found. Please ensure the following files exist:\n  {file1_path}\n  {file2_path}")
        return None
    except Exception as e:
        print(f"An error occurred while opening the files: {e}")
        return None

    sheet_names1 = set(excel_file1.sheet_names)
    sheet_names2 = set(excel_file2.sheet_names)
    all_sheet_names = sorted(sheet_names1.union(sheet_names2))

    # This is the dictionary where results are stored
    comparison_results = {}
    found_difference = False # Flag to track if any differences were found

    for sheet_name in all_sheet_names:
        try:
            df1 = excel_file1.parse(sheet_name) if sheet_name in sheet_names1 else None
            df2 = excel_file2.parse(sheet_name) if sheet_name in sheet_names2 else None
        except Exception as e:
            # Report error only if it occurs for a sheet that might be different
            print(f"\nComparing sheet: '{sheet_name}'")
            print(f"  Error reading sheet '{sheet_name}': {e}")
            comparison_results[sheet_name] = False
            found_difference = True
            continue # Move to the next sheet

        is_different = False # Flag for the current sheet

        if df1 is None:
            if sheet_name in sheet_names2: # Only report if it exists in the other file
                 print(f"\nComparing sheet: '{sheet_name}'")
                 print(f"  Sheet '{sheet_name}' is only present in {os.path.basename(file2_path)}.")
                 comparison_results[sheet_name] = False
                 is_different = True
            else: # Sheet not in either, skip adding it to results
                 continue
        elif df2 is None:
            if sheet_name in sheet_names1: # Only report if it exists in the other file
                print(f"\nComparing sheet: '{sheet_name}'")
                print(f"  Sheet '{sheet_name}' is only present in {os.path.basename(file1_path)}.")
                comparison_results[sheet_name] = False
                is_different = True
            else: # Sheet not in either, skip adding it to results
                 continue
        elif not df1.equals(df2):
            print(f"\nComparing sheet: '{sheet_name}'")
            print("  Sheets are different.")
            comparison_results[sheet_name] = False
            is_different = True
            # Provide more details on differences
            if not df1.shape == df2.shape:
                print(f"    Shape mismatch: {df1.shape} vs {df2.shape}")
            else:
                # Find the first difference.
                # Fill NaN values with a placeholder to allow comparison, then compare
                # Use a placeholder unlikely to exist in the data
                placeholder = "___NaN___"
                df1_filled = df1.fillna(placeholder)
                df2_filled = df2.fillna(placeholder)
                diff_mask = (df1_filled != df2_filled) & ~(df1.isna() & df2.isna()) # Ignore if both are NaN

                # Get locations where diff_mask is True
                diff_indices = diff_mask.stack()
                diff_loc = diff_indices[diff_indices].index.tolist()

                if diff_loc:
                    first_diff_row, first_diff_col = diff_loc[0]
                    # Get original values (could be NaN)
                    # Ensure column index is valid before accessing iloc
                    col_idx1 = df1.columns.get_loc(first_diff_col)
                    col_idx2 = df2.columns.get_loc(first_diff_col)
                    val1 = df1.iloc[first_diff_row, col_idx1]
                    val2 = df2.iloc[first_diff_row, col_idx2]
                    print(f"    First difference at: Row {first_diff_row}, Column '{first_diff_col}'")
                    print(f"    Value in {os.path.basename(file1_path)}: {val1}")
                    print(f"    Value in {os.path.basename(file2_path)}: {val2}")
                else:
                    # This case might occur if differences are only in NaN patterns
                    # or data types, which .equals() catches but the element-wise check might miss.
                     print("    Differences detected by pandas.equals(), but no specific cell mismatch found with current logic (might involve NaNs or dtypes).")

        else:
            # Sheets are identical, store True but don't print anything here
            comparison_results[sheet_name] = True

        if is_different:
            found_difference = True # Mark that at least one difference was reported

    # Final Summary - Only report if differences were found
    if found_difference:
        print("\nSummary of Differing Sheets:")
        # *** FIX: Use comparison_results instead of results ***
        diff_sheets = [sheet for sheet, identical in comparison_results.items() if not identical]
        if diff_sheets:
            for sheet in diff_sheets:
                print(f"  - {sheet}")
        # No need for an else here, as we only print the summary if found_difference is True
    else:
        print("\nAll comparable sheets are identical.")


    return comparison_results

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python compare_excel.py <excel_file_name>")
        sys.exit(1)
    filename = sys.argv[1]
    # The function call itself is correct, the error was inside the function
    results = compare_excel_files(filename)
    # The function now handles printing the summary, so no extra print needed here
    # unless you want to use the 'results' dictionary for something else.
