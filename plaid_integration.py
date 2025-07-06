#!/usr/bin/env python3
"""
Plaid API Integration for MoneyMage
This script provides automatic transaction fetching from banks using the Plaid API
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
from dataclasses import dataclass

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from transactions import update_old_transactions, get_old_transactions
from excel_management import write_transactions_xlsx


@dataclass
class PlaidConfig:
    """Configuration for Plaid API"""
    client_id: str
    secret: str
    environment: str = "sandbox"  # sandbox, development, production
    products: List[str] = None
    country_codes: List[str] = None
    
    def __post_init__(self):
        if self.products is None:
            self.products = ["transactions"]
        if self.country_codes is None:
            self.country_codes = ["US"]


class PlaidTransactionFetcher:
    """Handles transaction fetching from Plaid API"""
    
    def __init__(self, config_file: str = "plaid_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.setup_logging()
        
        # Plaid API endpoints
        self.base_urls = {
            "sandbox": "https://sandbox.plaid.com",
            "development": "https://development.plaid.com",
            "production": "https://production.plaid.com"
        }
        self.base_url = self.base_urls[self.config.environment]
        
        # Common headers for API requests
        self.headers = {
            "Content-Type": "application/json",
            "PLAID-CLIENT-ID": self.config.client_id,
            "PLAID-SECRET": self.config.secret
        }
    
    def load_config(self) -> PlaidConfig:
        """Load Plaid configuration from JSON file"""
        default_config = {
            "client_id": "",
            "secret": "",
            "environment": "sandbox",
            "products": ["transactions"],
            "country_codes": ["US"],
            "access_tokens": {},  # Store access tokens for different accounts
            "account_mapping": {}  # Map Plaid account IDs to your internal account names
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                
                return PlaidConfig(
                    client_id=config_data.get("client_id", ""),
                    secret=config_data.get("secret", ""),
                    environment=config_data.get("environment", "sandbox"),
                    products=config_data.get("products", ["transactions"]),
                    country_codes=config_data.get("country_codes", ["US"])
                )
            except Exception as e:
                print(f"Error loading Plaid config: {e}")
                self.create_default_config(default_config)
                return PlaidConfig(client_id="", secret="")
        else:
            self.create_default_config(default_config)
            return PlaidConfig(client_id="", secret="")
    
    def create_default_config(self, default_config: dict):
        """Create default configuration file"""
        with open(self.config_file, 'w') as f:
            json.dump(default_config, f, indent=2)
        print(f"Created default Plaid config file: {self.config_file}")
        print("Please add your Plaid credentials to the config file.")
    
    def setup_logging(self):
        """Setup logging configuration"""
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/plaid_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def create_link_token(self, user_id: str) -> Optional[str]:
        """Create a link token for Plaid Link initialization"""
        request_data = {
            "client_id": self.config.client_id,
            "secret": self.config.secret,
            "client_name": "MoneyMage",
            "products": self.config.products,
            "country_codes": self.config.country_codes,
            "language": "en",
            "user": {
                "client_user_id": user_id
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/link/token/create",
                json=request_data,
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("link_token")
            else:
                self.logger.error(f"Failed to create link token: {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating link token: {e}")
            return None
    
    def exchange_public_token(self, public_token: str) -> Optional[str]:
        """Exchange public token for access token"""
        request_data = {
            "client_id": self.config.client_id,
            "secret": self.config.secret,
            "public_token": public_token
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/link/token/exchange",
                json=request_data,
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("access_token")
            else:
                self.logger.error(f"Failed to exchange public token: {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error exchanging public token: {e}")
            return None
    
    def get_accounts(self, access_token: str) -> List[Dict]:
        """Get account information"""
        request_data = {
            "client_id": self.config.client_id,
            "secret": self.config.secret,
            "access_token": access_token
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/accounts/get",
                json=request_data,
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("accounts", [])
            else:
                self.logger.error(f"Failed to get accounts: {response.text}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting accounts: {e}")
            return []
    
    def get_transactions(self, access_token: str, start_date: datetime, end_date: datetime, 
                        account_ids: Optional[List[str]] = None) -> List[Dict]:
        """Get transactions for specified date range"""
        request_data = {
            "client_id": self.config.client_id,
            "secret": self.config.secret,
            "access_token": access_token,
            "start_date": start_date.date().isoformat(),
            "end_date": end_date.date().isoformat()
        }
        
        if account_ids:
            request_data["account_ids"] = account_ids
        
        try:
            response = requests.post(
                f"{self.base_url}/transactions/get",
                json=request_data,
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("transactions", [])
            else:
                self.logger.error(f"Failed to get transactions: {response.text}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting transactions: {e}")
            return []
    
    def convert_plaid_to_moneymage_format(self, transactions: List[Dict], 
                                        account_mapping: Dict[str, str]) -> Dict[str, List]:
        """Convert Plaid transactions to MoneyMage format"""
        converted_transactions = {
            'Date': [],
            'Amount': [],
            'Category': [],
            'Account': [],
            'Description': [],
            'R': [],
            'Notes': []
        }
        
        for transaction in transactions:
            # Convert date
            trans_date = datetime.strptime(transaction['date'], '%Y-%m-%d').date()
            converted_transactions['Date'].append(trans_date)
            
            # Convert amount (Plaid amounts are positive for debits, negative for credits)
            # MoneyMage uses negative for expenses, positive for income
            amount = -transaction['amount']  # Flip the sign
            converted_transactions['Amount'].append(amount)
            
            # Get account name from mapping
            account_id = transaction['account_id']
            account_name = account_mapping.get(account_id, f"plaid_account_{account_id[:8]}")
            converted_transactions['Account'].append(account_name)
            
            # Get description
            description = transaction.get('name', 'Unknown Transaction')
            converted_transactions['Description'].append(description)
            
            # Set category as uncategorized (will be auto-categorized later)
            converted_transactions['Category'].append('uncategorized')
            
            # Empty R and Notes fields
            converted_transactions['R'].append('')
            converted_transactions['Notes'].append('')
        
        return converted_transactions
    
    def fetch_and_process_transactions(self, days_back: int = 30) -> bool:
        """Fetch transactions from all configured accounts and process them"""
        # Load full config with access tokens
        with open(self.config_file, 'r') as f:
            full_config = json.load(f)
        
        access_tokens = full_config.get('access_tokens', {})
        account_mapping = full_config.get('account_mapping', {})
        
        if not access_tokens:
            self.logger.error("No access tokens found. Please run setup first.")
            return False
        
        # Date range for fetching transactions
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        all_transactions = {
            'Date': [],
            'Amount': [],
            'Category': [],
            'Account': [],
            'Description': [],
            'R': [],
            'Notes': []
        }
        
        # Fetch transactions from each account
        for account_name, access_token in access_tokens.items():
            try:
                self.logger.info(f"Fetching transactions for account: {account_name}")
                
                # Get account IDs first
                accounts = self.get_accounts(access_token)
                if not accounts:
                    self.logger.warning(f"No accounts found for {account_name}")
                    continue
                
                # Get transactions
                transactions = self.get_transactions(access_token, start_date, end_date)
                
                if transactions:
                    self.logger.info(f"Found {len(transactions)} transactions for {account_name}")
                    
                    # Convert to MoneyMage format
                    converted = self.convert_plaid_to_moneymage_format(transactions, account_mapping)
                    
                    # Merge with all transactions
                    for key in all_transactions.keys():
                        all_transactions[key].extend(converted[key])
                else:
                    self.logger.info(f"No transactions found for {account_name}")
                    
            except Exception as e:
                self.logger.error(f"Error processing account {account_name}: {e}")
                continue
        
        if not all_transactions['Date']:
            self.logger.info("No transactions found from any account")
            return True
        
        # Process transactions through existing MoneyMage logic
        try:
            # Get old transactions
            _, old_transactions = get_old_transactions('transactions.xlsx')
            
            # Update with new transactions
            updated_transactions = update_old_transactions(all_transactions, old_transactions)
            
            self.logger.info(f"Successfully processed {len(all_transactions['Date'])} transactions from Plaid")
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing transactions: {e}")
            return False
    
    def setup_account_link(self, account_name: str, user_id: str = "default_user") -> str:
        """Setup account linking - returns link token for frontend"""
        if not self.config.client_id or not self.config.secret:
            raise ValueError("Plaid credentials not configured. Please update plaid_config.json")
        
        link_token = self.create_link_token(user_id)
        if not link_token:
            raise RuntimeError("Failed to create link token")
        
        print(f"Link token created for account '{account_name}': {link_token}")
        print("\nTo complete the setup:")
        print("1. Use this link token in Plaid Link to connect your bank account")
        print("2. After successful connection, you'll receive a public token")
        print("3. Run: python plaid_integration.py --save-token <account_name> <public_token>")
        
        return link_token
    
    def save_access_token(self, account_name: str, public_token: str) -> bool:
        """Save access token after successful bank connection"""
        access_token = self.exchange_public_token(public_token)
        if not access_token:
            self.logger.error("Failed to exchange public token for access token")
            return False
        
        # Load existing config
        with open(self.config_file, 'r') as f:
            config_data = json.load(f)
        
        # Add access token
        if 'access_tokens' not in config_data:
            config_data['access_tokens'] = {}
        
        config_data['access_tokens'][account_name] = access_token
        
        # Get account information for mapping
        accounts = self.get_accounts(access_token)
        if accounts:
            if 'account_mapping' not in config_data:
                config_data['account_mapping'] = {}
            
            for account in accounts:
                account_id = account['account_id']
                account_desc = f"{account['name']} ({account['subtype']})"
                config_data['account_mapping'][account_id] = account_desc
                print(f"Added account mapping: {account_id} -> {account_desc}")
        
        # Save updated config
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        self.logger.info(f"Successfully saved access token for account: {account_name}")
        return True


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MoneyMage Plaid Integration')
    parser.add_argument('--setup', type=str, help='Setup new account link (provide account name)')
    parser.add_argument('--save-token', nargs=2, metavar=('ACCOUNT_NAME', 'PUBLIC_TOKEN'),
                        help='Save access token after bank connection')
    parser.add_argument('--fetch', type=int, default=30, metavar='DAYS',
                        help='Fetch transactions from last N days (default: 30)')
    parser.add_argument('--list-accounts', action='store_true',
                        help='List configured accounts')
    
    args = parser.parse_args()
    
    fetcher = PlaidTransactionFetcher()
    
    if args.setup:
        try:
            link_token = fetcher.setup_account_link(args.setup)
            print(f"Setup initiated for account: {args.setup}")
        except Exception as e:
            print(f"Error setting up account: {e}")
    
    elif args.save_token:
        account_name, public_token = args.save_token
        if fetcher.save_access_token(account_name, public_token):
            print(f"Successfully configured account: {account_name}")
        else:
            print(f"Failed to configure account: {account_name}")
    
    elif args.list_accounts:
        try:
            with open(fetcher.config_file, 'r') as f:
                config_data = json.load(f)
            
            access_tokens = config_data.get('access_tokens', {})
            print("Configured accounts:")
            for account_name in access_tokens.keys():
                print(f"  - {account_name}")
        except Exception as e:
            print(f"Error listing accounts: {e}")
    
    else:
        # Fetch transactions
        print(f"Fetching transactions from last {args.fetch} days...")
        success = fetcher.fetch_and_process_transactions(args.fetch)
        if success:
            print("Transaction fetch completed successfully")
        else:
            print("Transaction fetch failed")


if __name__ == "__main__":
    main() 