import os.path
from datetime import datetime
import pandas as pd
from utilities import cat_lists, similar
from excel_management import write_transactions_xlsx
import glob
from itertools import combinations
import re


def get_new_transactions():

    import platform
    if platform.system() == 'Darwin':
        # Temporarily using current directory instead of Downloads due to permission issues
        downloads_dir = './'  # Changed from '/Users/tslowery/Downloads/'
    else:
        downloads_dir = 'C:\\Users\\tslow\\Downloads\\'
    
    try:
        wf_file = glob.glob(f'{downloads_dir}CreditCard*.csv')[0]
    except IndexError:
        wf_file = ''
    
    try:
        chase_files = sorted(glob.glob(f'{downloads_dir}Chase3376_Activity_*.CSV'))
        if chase_files:
            chase_file = chase_files[-1]
        else:
            chase_file = ''
    except IndexError:
        chase_file = ''
    
    try:
        rr_file = glob.glob(f'{downloads_dir}Chase9*_Activity_*.csv')[0]
    except IndexError:
        rr_file = ''
    
    try:
        ally_file = glob.glob(f'{downloads_dir}transactions*.csv')[0]
    except IndexError:
        ally_file = ''

    # Get the transactions
    # WF Active
    wf_dates =[]
    wf_desc = []
    wf_amounts = []
    wf_account = []
    try:
        with open(wf_file) as f:
            lines = f.read().splitlines()
        wf_dates = [datetime.strptime(x.split(',')[0].replace('"', ''), '%m/%d/%Y').date() for x in lines]
        wf_amounts = [float(x.split(',')[1].replace('"', '')) for x in lines]
        wf_desc = [x.split(',')[4].replace('"', '') for x in lines]
        wf_account = ['wf active']*len(wf_desc)
    except FileNotFoundError:
        print('No wf active transactions found')

    # Ally
    a_dates =[]
    a_desc = []
    a_amounts = []
    a_account = []
    try:
        with open(ally_file) as f:
            lines = f.read().splitlines()
        a_dates = [datetime.strptime(x.split(',')[0], '%Y-%m-%d').date() for x in lines[1:]]
        a_amounts = [float(x.split(',')[2]) for x in lines[1:]]
        a_desc = [x.split(',')[4] for x in lines[1:]]
        a_account = ['ally']*len(a_desc)
    except FileNotFoundError:
        print('No ally transactions found')

    # Chase RR
    rr_dates =[]
    rr_desc = []
    rr_amounts = []
    rr_account = []
    try:
        with open(rr_file) as f:
            lines = f.read().splitlines()
        rr_dates = [datetime.strptime(x.split(',')[0], '%m/%d/%Y').date() for x in lines[1:]]
        rr_desc = [x.split(',')[2] for x in lines[1:]]
        rr_amounts = [float(x.split(',')[5]) for x in lines[1:]]
        rr_account = ['chase_rr']*len(rr_amounts)
    except FileNotFoundError:
        print('No Chase RR transactions found')

    # Chase Checking
    cc_dates =[]
    cc_desc = []
    cc_amounts = []
    cc_account = []
    try:
        with open(chase_file) as f:
            lines = f.read().splitlines()
        cc_dates = [datetime.strptime(x.split(',')[1], '%m/%d/%Y').date() for x in lines[1:]]
        cc_desc = [x.split(',')[2] for x in lines[1:]]
        cc_amounts = [float(x.split(',')[3]) for x in lines[1:]]
        cc_account = ['chase_checking']*len(cc_amounts)
    except FileNotFoundError:
        print('No chase checking transactions found')

    # Combine all lists
    trans_dates = cat_lists(a_dates, rr_dates, cc_dates, wf_dates)
    trans_desc = cat_lists(a_desc, rr_desc, cc_desc, wf_desc)
    trans_amounts = cat_lists(a_amounts, rr_amounts, cc_amounts, wf_amounts)
    trans_account = cat_lists(a_account, rr_account, cc_account, wf_account)
    if len(trans_dates) != len(trans_desc) != len(trans_amounts):
        raise Exception('trans lists are not equal len')
    trans_categories = ['uncategorized']*len(trans_dates)
    zipped = list(zip(trans_dates, trans_amounts, trans_categories, trans_desc, trans_account))
    zipped.sort()
    out_dict = {
        'Date': [x[0] for x in zipped],
        'Amount': [x[1] for x in zipped],
        'Category': [x[2] for x in zipped],
        'Account': [x[4] for x in zipped],
        'Description': [x[3] for x in zipped],
        'R': ['']*len(zipped),
        'Notes': ['']*len(zipped)
    }
    print('here')

    # Auto categorize
    b = pd.ExcelFile('auto_categories.xlsx')
    df_auto_cats = b.parse()
    auto_cats = df_auto_cats.to_dict('list')
    b.close()
    auto_categorized = out_dict['Category']
    for i, desc in enumerate(out_dict['Description']):
        for a, auto_cat in enumerate(auto_cats['Category']):
            if similar(desc, auto_cats['Description'][a]) > 0.7:
                auto_categorized[i] = auto_cat
                break
    out_dict['Category'] = auto_categorized

    return out_dict


def extract_chase_id(description):
    """Extracts a unique ID from a Chase transaction description."""
    # Patterns for different ID formats in Chase descriptions, ordered by specificity
    patterns = [
        r'ORIG ID:(\w+)',
        r'PPD ID:\s*(\w+)',
        r'ID\s+(\w+)',
        r'ref\s+(\w+)',
        r'(\w{10,})'  # General-purpose: find any long alphanumeric string
    ]
    for pattern in patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def update_old_transactions(new_transactions, old_transactions):
    """Function to update the existing transactions xlsx"""

    # Remove the new transactions that are duplicates of old transactions
    new_transactions_descriptions = new_transactions['Description']
    new_transactions['Description'] = [x.replace('"', '') for x in new_transactions_descriptions]
    
    for d, date_value in enumerate(new_transactions['Date']):
        # Find all old transactions on the same date
        i_same_date = [i for i, x in enumerate(old_transactions['Date']) if x == date_value]
        
        if i_same_date:
            # print(f"Debug: Checking new transaction: {new_transactions['Description'][d]} = ${new_transactions['Amount'][d]} on {date_value}")
            
            # Special handling for Chase transactions using unique IDs
            is_new_chase = 'chase' in new_transactions['Account'][d].lower()
            if is_new_chase:
                new_chase_id = extract_chase_id(new_transactions['Description'][d])
                if new_chase_id:
                    for i in i_same_date:
                        is_old_chase = 'chase' in old_transactions['Account'][i].lower()
                        if is_old_chase:
                            old_chase_id = extract_chase_id(old_transactions['Description'][i])
                            amount_match = abs(new_transactions['Amount'][d] - old_transactions['Amount'][i]) < 0.01
                            if old_chase_id and old_chase_id == new_chase_id and amount_match:
                                # print(f"  -> Chase ID match duplicate found (ID: {new_chase_id}), marking as 'd'")
                                new_transactions['R'][d] = 'd'
                                break  # Move to the next new transaction
            
            # If already marked as duplicate, skip further checks
            if new_transactions['R'][d] == 'd':
                continue

            # First, check for split transaction scenario (prioritize this over exact matches)
            # Find all transactions with similar descriptions on the same date
            similar_transactions = []
            exact_match_transaction = None
            
            for i in i_same_date:
                similarity_score = similar(new_transactions['Description'][d], old_transactions['Description'][i])
                amount_match = abs(new_transactions['Amount'][d] - old_transactions['Amount'][i]) < 0.01
                
                # print(f"  vs old: {old_transactions['Description'][i]} = ${old_transactions['Amount'][i]}, similarity: {similarity_score:.2f}, amount_match: {amount_match}")
                
                # Track exact matches but don't immediately mark as duplicate
                if similarity_score >= 0.8 and amount_match:
                    exact_match_transaction = i
                
                # Collect similar transactions for split detection
                if similarity_score >= 0.7:
                    similar_transactions.append({
                        'index': i,
                        'amount': old_transactions['Amount'][i],
                        'description': old_transactions['Description'][i],
                        'similarity': similarity_score,
                        'notes': old_transactions['Notes'][i] if 'Notes' in old_transactions else '',
                        'r_flag': old_transactions['R'][i] if 'R' in old_transactions else ''
                    })
            
            # Check for split transaction scenario first
            split_detected = False
            if len(similar_transactions) > 1:  # Must have multiple similar transactions for split
                # print(f"  Found {len(similar_transactions)} similar transactions:")
                # for st in similar_transactions:
                    # print(f"    {st['description']} = ${st['amount']} (similarity: {st['similarity']:.2f}, R: '{st['r_flag']}')")
                
                # Calculate sum of similar transactions (excluding exact matches from the sum)
                split_transactions = [st for st in similar_transactions if abs(st['amount'] - new_transactions['Amount'][d]) >= 0.01]
                total_amount = sum(st['amount'] for st in split_transactions)
                amount_diff = abs(abs(new_transactions['Amount'][d]) - abs(total_amount))
                
                # print(f"  Split transactions sum: ${total_amount}")
                # print(f"  New transaction amount: ${new_transactions['Amount'][d]}")
                # print(f"  Difference: ${amount_diff}")
                
                # Check for split markers
                has_split_marker = any(
                    'x' in str(st['r_flag']).lower() or 
                    'split' in str(st['notes']).lower()
                    for st in split_transactions
                )
                
                # If the sum matches and there are split markers, it's a split transaction
                if amount_diff < 0.01 and has_split_marker and len(split_transactions) >= 2:
                    # print(f"  -> Split transaction detected (sum match + split markers), marking as 'd'")
                    new_transactions['R'][d] = 'd'
                    split_detected = True
                # Alternative: if there are multiple split transactions with markers
                elif has_split_marker and len(split_transactions) >= 2:
                    # print(f"  -> Split transaction detected (multiple split markers), marking as 'd'")
                    new_transactions['R'][d] = 'd'
                    split_detected = True
            
            # Only check for exact match if no split was detected
            if not split_detected and exact_match_transaction is not None:
                # Check if this exact match might be the original of a split transaction
                exact_match_has_splits = False
                if len(similar_transactions) > 1:
                    # Check if there are other similar transactions with split markers
                    other_similar = [st for st in similar_transactions if st['index'] != exact_match_transaction]
                    if any('x' in str(st['r_flag']).lower() for st in other_similar):
                        exact_match_has_splits = True
                        # print(f"  -> Exact match found, but other split transactions exist - treating as split duplicate")
                
                if not exact_match_has_splits:
                    # print(f"  -> Exact duplicate found, marking as 'd'")
                    new_transactions['R'][d] = 'd'
                else:
                    # print(f"  -> Exact match found but treating as split transaction duplicate")
                    new_transactions['R'][d] = 'd'
        
        elif new_transactions['Account'][d] == 'chase_checking':
            pass
            # print(f"  No old transactions found on this date.")

    # Report summary
    duplicates_found = sum(1 for r in new_transactions['R'] if r == 'd')
    print(f"Summary: Found {duplicates_found} duplicate transactions out of {len(new_transactions['Date'])} new transactions")

    new_transactions_no_duplicates = {}
    for item, i_list in new_transactions.items():
        new_transactions_no_duplicates[item] = []
        for i, x in enumerate(i_list):
            if new_transactions['R'][i] != 'd':
                 new_transactions_no_duplicates[item].append(x)

    # Update transactions
    transactions_updated = {}
    for item, t_list in old_transactions.items():
        new_list = t_list.copy()
        new_list.extend(new_transactions_no_duplicates[item])
        transactions_updated[item] = new_list

    # Sort by Date
    zipped = list(zip(transactions_updated['Date'], transactions_updated['Amount'], transactions_updated['Category'],
                      transactions_updated['Account'], transactions_updated['Description'], transactions_updated['R'],
                      transactions_updated['Notes']))
    zipped.sort()
    transactions = {}
    for i, key in enumerate(transactions_updated.keys()):
        transactions[key] = [x[i] for x in zipped]

    # Clean up split transactions BEFORE writing the file
    transactions = clean_split_transactions(transactions)

    # Recreate the transactions xlsx with the updated transactions
    write_transactions_xlsx(transactions.copy(), new_transactions)

    return transactions


def get_old_transactions(transactions_xlsx):
    """Function to get the old transactions from the transactions xlsx"""

    if not os.path.exists(transactions_xlsx):
        return None, {'Date': [], 'Amount': [], 'Category': [], 'Account': [], 'Description': [],
                      'R': [], 'Notes': []}
    f = pd.ExcelFile(transactions_xlsx)
    df = f.parse(sheet_name='Transactions')
    df.fillna('', inplace=True)
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    df.sort_values('Date', inplace=True)
    old_transactions = df.to_dict('list')
    
    # Handle potential mixed types in the Date column
    converted_dates = []
    for x in old_transactions['Date']:
        if pd.isna(x):
            # Handle NaN values
            converted_dates.append(None)
        elif isinstance(x, (int, float)):
            # Handle numeric values by converting them to datetime
            try:
                dt = pd.to_datetime(x)
                converted_dates.append(dt.date())
            except:
                # If conversion fails, use None
                converted_dates.append(None)
        else:
            # Handle datetime objects
            try:
                converted_dates.append(x.to_pydatetime().date())
            except AttributeError:
                # Fallback for any other types
                try:
                    dt = pd.to_datetime(x)
                    converted_dates.append(dt.date())
                except:
                    converted_dates.append(None)
    
    old_transactions['Date'] = converted_dates

    return f, old_transactions


def get_transactions(transactions_xlsx):
    """Function to get the transactions for the budget"""

    # Get the new transactions from bank transactions downloads
    new_transactions = get_new_transactions()

    # Get the old transactions from the transactions xlsx
    f, old_transactions = get_old_transactions(transactions_xlsx)

    # Always attempt to update transactions, duplicate handling is done inside update_old_transactions
    transactions = update_old_transactions(new_transactions.copy(), old_transactions)

    return transactions


def clean_split_transactions(transactions):
    """Remove uncategorized transactions that have been split into multiple categorized transactions"""
    
    print("Cleaning up split transactions...")
    
    # Create a list to track transactions to remove
    transactions_to_remove = []
    
    # Group transactions by date
    date_groups = {}
    for i, date in enumerate(transactions['Date']):
        if date not in date_groups:
            date_groups[date] = []
        date_groups[date].append(i)
    
    # Check each date group for split transaction scenarios
    for date, indices in date_groups.items():
        # Find uncategorized transactions on this date
        uncategorized_indices = [i for i in indices if transactions['Category'][i] == 'uncategorized']
        
        for unc_idx in uncategorized_indices:
            unc_desc = transactions['Description'][unc_idx]
            unc_amount = transactions['Amount'][unc_idx]
            unc_account = transactions['Account'][unc_idx]
            
            # Find similar transactions on the same date with 'x' markers
            split_candidates = []
            for i in indices:
                if i == unc_idx:  # Skip the uncategorized transaction itself
                    continue
                    
                # Check if this could be a split transaction
                if (similar(unc_desc, transactions['Description'][i]) >= 0.9 and  # Very similar description
                    transactions['Account'][i] == unc_account and  # Same account
                    transactions['Category'][i] != 'uncategorized' and  # Is categorized
                    str(transactions['R'][i]).lower() == 'x'):  # Has split marker
                    
                    split_candidates.append({
                        'index': i,
                        'amount': transactions['Amount'][i],
                        'category': transactions['Category'][i],
                        'description': transactions['Description'][i]
                    })
            
            # If we found split candidates, check if they sum to the uncategorized amount
            if len(split_candidates) >= 2:  # Must have at least 2 split transactions
                print(f"  Checking uncategorized: {unc_desc} = ${unc_amount} on {date}")
                print(f"    Found {len(split_candidates)} split candidates:")
                for sc in split_candidates:
                    print(f"      ${sc['amount']} -> {sc['category']}")
                
                # Try different combinations of split candidates to find exact matches
                found_exact_split = False
                for r in range(2, len(split_candidates) + 1):
                    for combo in combinations(split_candidates, r):
                        combo_sum = sum(sc['amount'] for sc in combo)
                        amount_diff = abs(abs(unc_amount) - abs(combo_sum))
                        
                        if amount_diff < 0.01:  # Amounts match within tolerance
                            print(f"    -> Found exact split match with {len(combo)} transactions:")
                            for sc in combo:
                                print(f"       ${sc['amount']} -> {sc['category']}")
                            print(f"    -> Total: ${combo_sum} matches ${unc_amount}")
                            
                            # Mark this uncategorized transaction for removal
                            transactions_to_remove.append(unc_idx)
                            found_exact_split = True
                            break
                    
                    if found_exact_split:
                        break
                
                if not found_exact_split:
                    print(f"    -> No exact split match found")
    
    # Remove the identified transactions (in reverse order to maintain indices)
    transactions_to_remove.sort(reverse=True)
    
    if transactions_to_remove:
        print(f"\nRemoving {len(transactions_to_remove)} uncategorized transactions that have been split:")
        
        # Create new transaction lists without the removed transactions
        cleaned_transactions = {}
        for key in transactions.keys():
            cleaned_transactions[key] = []
            for i, value in enumerate(transactions[key]):
                if i not in transactions_to_remove:
                    cleaned_transactions[key].append(value)
        
        # Show what was removed
        for idx in sorted(transactions_to_remove):
            print(f"  Removed: {transactions['Date'][idx]} {transactions['Description'][idx]} = ${transactions['Amount'][idx]}")
        
        return cleaned_transactions
    else:
        print("  No split transactions found to clean up")
        return transactions
