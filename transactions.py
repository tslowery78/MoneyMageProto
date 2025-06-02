import os.path
from datetime import datetime
import pandas as pd
from utilities import cat_lists, similar
from excel_management import write_transactions_xlsx
import glob


def get_new_transactions():

    import platform
    if platform.system() == 'Darwin':
        # Temporarily using current directory instead of Downloads due to permission issues
        downloads_dir = './'  # Changed from '/Users/tslowery/Downloads/'
    else:
        downloads_dir = 'C:\\Users\\tslow\\Downloads\\'
    
    print(f"Debug: downloads_dir = {downloads_dir}")
    
    try:
        wf_matches = glob.glob(f'{downloads_dir}CreditCard*.csv')
        print(f"Debug: WF matches = {wf_matches}")
        wf_file = wf_matches[0]
        print(f"Debug: wf_file = {wf_file}")
    except IndexError:
        wf_file = ''
        print("Debug: No WF file found")
    
    try:
        chase_matches = sorted(glob.glob(f'{downloads_dir}Chase3376_Activity_*.CSV'))
        print(f"Debug: Chase matches = {chase_matches}")
        if chase_matches:
            chase_file = chase_matches[-1]
            print(f"Debug: chase_file = {chase_file}")
        else:
            chase_file = ''
            print("Debug: No Chase files in sorted list")
    except IndexError:
        chase_file = ''
        print("Debug: IndexError for Chase files")
    print(f"Debug: chase_file path found: {chase_file}")
    
    try:
        rr_matches = glob.glob(f'{downloads_dir}Chase9*_Activity_*.csv')
        print(f"Debug: RR matches = {rr_matches}")
        rr_file = rr_matches[0]
        print(f"Debug: rr_file = {rr_file}")
    except IndexError:
        rr_file = ''
        print("Debug: No RR file found")
    
    try:
        ally_matches = glob.glob(f'{downloads_dir}transactions*.csv')
        print(f"Debug: Ally matches = {ally_matches}")
        ally_file = ally_matches[0]
        print(f"Debug: ally_file = {ally_file}")
    except IndexError:
        ally_file = ''
        print("Debug: No Ally file found")

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


def update_old_transactions(new_transactions, old_transactions):
    """Function to update the existing transactions xlsx"""

    # Remove the new transactions that are duplicates of old transactions
    new_transactions_descriptions = new_transactions['Description']
    new_transactions['Description'] = [x.replace('"', '') for x in new_transactions_descriptions]
    for d, date_value in enumerate(new_transactions['Date']):
        i_same_date = [i for i, x in enumerate(old_transactions['Date']) if x == date_value]
        if i_same_date:
            amount_sum = 0
            for c, i in enumerate(i_same_date):
                similarity_score = similar(new_transactions['Description'][d], old_transactions['Description'][i])
                amount_match = new_transactions['Amount'][d] == old_transactions['Amount'][i]

                if similarity_score >= 0.5:
                    if amount_match:
                        new_transactions['R'][d] = 'd'
                        break
                    amount_sum += old_transactions['Amount'][i]
                if c == len(i_same_date) - 1:
                    amount_diff = abs(abs(new_transactions['Amount'][d]) - abs(amount_sum))
                    if amount_diff < 0.001:
                        new_transactions['R'][d] = 'd'
        elif new_transactions['Account'][d] == 'chase_checking':
             print(f"  No old transactions found on this date.")


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
