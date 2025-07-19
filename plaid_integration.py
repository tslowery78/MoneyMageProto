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
import argparse

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
                f"{self.base_url}/item/public_token/exchange",
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
            
            # Use a default category for now
            converted_transactions['Category'].append('uncategorized')
            
            # Map Plaid account ID to internal account name
            account_name = account_mapping.get(transaction['account_id'], 'unknown_account')
            converted_transactions['Account'].append(account_name)
            
            # Use merchant name or name as description
            description = transaction.get('merchant_name') or transaction.get('name')
            converted_transactions['Description'].append(description)
            
            # Add placeholders for 'R' and 'Notes'
            converted_transactions['R'].append('')
            converted_transactions['Notes'].append('')
            
        return converted_transactions

    def fetch_new_transactions(self, days_back: int = 30) -> Optional[Dict[str, List]]:
        """
        Fetch new transactions from Plaid for all configured accounts.
        Returns a dictionary of new transactions if successful, otherwise None.
        """
        self.logger.info("Starting new transaction fetch from Plaid...")
        
        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            access_tokens = config_data.get("access_tokens", {})
            account_mapping = config_data.get("account_mapping", {})
        except FileNotFoundError:
            self.logger.error(f"Config file not found at {self.config_file}")
            self.create_default_config({})
            return None
        
        if not access_tokens:
            self.logger.warning("No access tokens found in config. Cannot fetch transactions.")
            return None
        
        all_new_transactions = {
            'Date': [], 'Amount': [], 'Category': [], 'Account': [],
            'Description': [], 'R': [], 'Notes': []
        }
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        for account_name, access_token in access_tokens.items():
            self.logger.info(f"Fetching transactions for {account_name}...")
            plaid_transactions = self.get_transactions(access_token, start_date, end_date)
            
            if plaid_transactions:
                new_trans = self.convert_plaid_to_moneymage_format(plaid_transactions, account_mapping)
                for key in all_new_transactions:
                    all_new_transactions[key].extend(new_trans[key])
        
        if not all_new_transactions['Date']:
            self.logger.info("No new transactions fetched from Plaid.")
            return None

        self.logger.info(f"Successfully fetched {len(all_new_transactions['Date'])} new transactions from Plaid.")
        return all_new_transactions

    def setup_account_link(self, account_name: str, user_id: str = "default_user") -> Optional[str]:
        """Initiate Plaid Link for a new account and return the link_token."""
        self.logger.info(f"Setting up new account link for '{account_name}'")
        link_token = self.create_link_token(user_id=user_id)
        
        if link_token:
            self.logger.info(f"Link token created for account '{account_name}': {link_token}")
            print(f"\nLink token created: {link_token}\n")
            print("To complete the setup:")
            print("1. Open plaid_link.html in a web browser.")
            print("2. Use this link token in Plaid Link to connect your bank account.")
            print("3. After successful connection, you'll receive a public token.")
            print("4. Paste the public token back here when prompted.")
        else:
            self.logger.error("Failed to create link token.")
            
        return link_token

    def save_access_token(self, account_name: str, public_token: str) -> bool:
        """Exchange public token for access token and save to config."""
        self.logger.info(f"Exchanging public token for access token for account '{account_name}'")
        access_token = self.exchange_public_token(public_token)
        
        if not access_token:
            self.logger.error("Could not retrieve access token.")
            return False
            
        self.logger.info(f"Successfully received access token for '{account_name}'.")
        
        # Load existing config data
        try:
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            self.logger.warning(f"Could not read config file, creating a new one. Error: {e}")
            config_data = {}
        
        # Update and save access token
        if "access_tokens" not in config_data:
            config_data["access_tokens"] = {}
        config_data["access_tokens"][account_name] = access_token
        
        # Get account information for mapping
        accounts = self.get_accounts(access_token)
        if accounts:
            if 'account_mapping' not in config_data:
                config_data['account_mapping'] = {}
            
            for account in accounts:
                account_id = account['account_id']
                account_desc = f"{account['name']} ({account.get('subtype', 'N/A')})"
                config_data['account_mapping'][account_id] = account_desc
                self.logger.info(f"Added account mapping: {account_id} -> {account_desc}")

        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            self.logger.info(f"Access token for '{account_name}' saved to {self.config_file}")
            return True
        except IOError as e:
            self.logger.error(f"Error writing to config file: {e}")
            return False

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Plaid Integration for MoneyMage")
    parser.add_argument(
        "--add-bank",
        metavar="ACCOUNT_NAME",
        type=str,
        help="Add a new bank account. Provide a friendly name for the account."
    )
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="Fetch new transactions from all linked accounts."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days back to fetch transactions for. Default is 30."
    )
    
    args = parser.parse_args()
    fetcher = PlaidTransactionFetcher()

    if args.add_bank:
        account_name = args.add_bank
        link_token = fetcher.setup_account_link(account_name)
        
        if link_token:
            public_token = input("--> Paste the public_token here and press Enter: ").strip()
            if public_token:
                if fetcher.save_access_token(account_name, public_token):
                    print("\nNew bank account added successfully!")
                    print("You can now fetch transactions using the --fetch flag.")
                else:
                    print("\nFailed to save the access token. Please try again.")
            else:
                print("\nNo public_token provided. Aborting.")
    
    elif args.fetch:
        print(f"Fetching transactions for the last {args.days} days...")
        all_transactions = fetcher.fetch_new_transactions(days_back=args.days)
        
        if all_transactions and any(len(tx_list) > 0 for tx_list in all_transactions.values() if isinstance(tx_list, list)):
            output_file = "transactions.xlsx"
            write_transactions_xlsx(all_transactions, output_file)
            print(f"Transactions saved to {output_file}")
        else:
            print("No new transactions found.")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()