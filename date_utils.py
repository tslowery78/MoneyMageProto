"""
Enhanced date parsing utilities for MoneyMageProto
Handles various Excel date formats including epoch timestamps and serial dates
"""

import datetime
import pandas as pd
from typing import Union, List, Any


def parse_date_robust(date_val: Any) -> datetime.date:
    """
    Robustly parse various date formats that might come from Excel or other sources.
    
    Handles:
    - String dates (MM/DD/YYYY format)
    - datetime/Timestamp objects  
    - Excel serial dates (days since 1899-12-30)
    - Unix timestamps (seconds, milliseconds, nanoseconds since epoch)
    - Date objects (pass through)
    
    Args:
        date_val: The value to convert to a date
        
    Returns:
        datetime.date object
        
    Raises:
        ValueError: If the date cannot be parsed
    """
    if pd.isna(date_val) or date_val == '':
        raise ValueError("Empty or NaN date value")
        
    # Already a date object
    if isinstance(date_val, datetime.date):
        return date_val
        
    # String format
    if isinstance(date_val, str):
        # Handle comma-separated values (take first part)
        clean_str = date_val.split(',')[0].strip()
        try:
            return datetime.datetime.strptime(clean_str, '%m/%d/%Y').date()
        except ValueError:
            # Try other common formats
            for fmt in ['%Y-%m-%d', '%m-%d-%Y', '%d/%m/%Y']:
                try:
                    return datetime.datetime.strptime(clean_str, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Cannot parse string date: {date_val}")
    
    # datetime or Timestamp objects
    if hasattr(date_val, 'date'):
        return date_val.date()
        
    # Numeric values (integers/floats)
    if isinstance(date_val, (int, float)):
        # Nanoseconds since epoch (very large numbers)
        if date_val > 1000000000000:
            timestamp_seconds = date_val / 1000000000
            return datetime.datetime.fromtimestamp(timestamp_seconds).date()
            
        # Milliseconds since epoch  
        elif date_val > 1000000000:
            timestamp_seconds = date_val / 1000
            return datetime.datetime.fromtimestamp(timestamp_seconds).date()
            
        # Excel serial date (days since 1899-12-30)
        elif date_val > 25000:
            base_date = datetime.date(1899, 12, 30)
            return base_date + datetime.timedelta(days=int(date_val))
            
        # Unix timestamp in seconds
        elif date_val > 0:
            try:
                return datetime.datetime.fromtimestamp(date_val).date()
            except (ValueError, OSError):
                raise ValueError(f"Ambiguous numeric date value: {date_val}")
        else:
            raise ValueError(f"Invalid numeric date value: {date_val}")
    
    raise ValueError(f"Unsupported date type: {type(date_val).__name__}")


def parse_dates_list(date_list: List[Any]) -> List[datetime.date]:
    """
    Parse a list of date values, providing detailed error messages for failures.
    
    Args:
        date_list: List of date values to parse
        
    Returns:
        List of datetime.date objects
        
    Raises:
        ValueError: If any date cannot be parsed, with details about the failure
    """
    parsed_dates = []
    
    for i, date_val in enumerate(date_list):
        # Skip empty strings and NaN values that somehow made it through
        if pd.isna(date_val) or date_val == '' or date_val is None:
            continue
            
        try:
            parsed_date = parse_date_robust(date_val)
            parsed_dates.append(parsed_date)
        except ValueError as e:
            # Provide helpful suggestion for common cases
            suggestion = ""
            if isinstance(date_val, (int, float)):
                try:
                    if date_val > 1000000000000:  # nanoseconds
                        suggested_date = datetime.datetime.fromtimestamp(date_val / 1000000000).date()
                        suggestion = f" (This might be {suggested_date.strftime('%m/%d/%Y')} - try reformatting the cell as a date)"
                    elif date_val > 25000:  # Excel serial
                        base_date = datetime.date(1899, 12, 30)
                        suggested_date = base_date + datetime.timedelta(days=int(date_val))
                        suggestion = f" (This might be {suggested_date.strftime('%m/%d/%Y')} - try reformatting the cell as a date)"
                except:
                    pass
            
            raise ValueError(
                f"Cannot parse date at position {i + 1}: '{date_val}' (type: {type(date_val).__name__}){suggestion}"
            ) from e
    
    return parsed_dates


def convert_pandas_dates(df: pd.DataFrame, date_columns: List[str]) -> pd.DataFrame:
    """
    Convert pandas DataFrame date columns to consistent datetime format.
    
    Args:
        df: DataFrame to process
        date_columns: List of column names to convert
        
    Returns:
        DataFrame with converted date columns
    """
    df_copy = df.copy()
    
    for col in date_columns:
        if col in df_copy.columns:
            # Use pandas to_datetime with errors='coerce' for robust conversion
            df_copy[col] = pd.to_datetime(df_copy[col], errors='coerce')
            
    return df_copy


def suggest_date_fix(problematic_value: Any) -> str:
    """
    Provide a helpful suggestion for fixing a problematic date value.
    
    Args:
        problematic_value: The value that couldn't be parsed
        
    Returns:
        String with suggestion for fixing the date
    """
    if isinstance(problematic_value, (int, float)):
        try:
            if problematic_value > 1000000000000:  # nanoseconds
                suggested_date = datetime.datetime.fromtimestamp(problematic_value / 1000000000).date()
                return f"This looks like a timestamp. Try reformatting the Excel cell as a date, or enter: {suggested_date.strftime('%m/%d/%Y')}"
            elif problematic_value > 25000:  # Excel serial
                base_date = datetime.date(1899, 12, 30)
                suggested_date = base_date + datetime.timedelta(days=int(problematic_value))
                return f"This looks like an Excel serial date. Try reformatting the cell as a date, or enter: {suggested_date.strftime('%m/%d/%Y')}"
            else:
                return "Try entering the date in MM/DD/YYYY format"
        except:
            return "Try entering the date in MM/DD/YYYY format"
    elif isinstance(problematic_value, str):
        return f"Could not parse '{problematic_value}'. Try using MM/DD/YYYY format"
    else:
        return "Try entering the date in MM/DD/YYYY format"
