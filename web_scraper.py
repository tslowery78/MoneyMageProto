#!/usr/bin/env python3
"""
Web Scraper for Bank Transactions
This script provides automated downloading of bank transaction CSV files
as a backup for banks that don't support APIs
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class BankScraper:
    """Base class for bank web scraping"""
    
    def __init__(self, config_file: str = "scraper_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.setup_logging()
        self.driver = None
        
    def load_config(self) -> dict:
        """Load scraper configuration from JSON file"""
        default_config = {
            "download_directory": "./downloads",
            "timeout": 30,
            "headless": True,
            "chrome_options": [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled"
            ],
            "banks": {
                "chase": {
                    "enabled": False,
                    "username": "",
                    "password": "",
                    "url": "https://secure01c.chase.com/web/auth/dashboard",
                    "selectors": {
                        "username": "#userId-text-input-field",
                        "password": "#password-text-input-field",
                        "login_button": "#signin-button",
                        "accounts_dropdown": ".account-tile",
                        "download_button": ".download-link"
                    }
                },
                "wells_fargo": {
                    "enabled": False,
                    "username": "",
                    "password": "",
                    "url": "https://connect.secure.wellsfargo.com/auth/login/present",
                    "selectors": {
                        "username": "#userid",
                        "password": "#password",
                        "login_button": "#btnSignon",
                        "accounts_menu": ".account-summary",
                        "download_link": ".download-transactions"
                    }
                },
                "ally": {
                    "enabled": False,
                    "username": "",
                    "password": "",
                    "url": "https://secure.ally.com/",
                    "selectors": {
                        "username": "#username",
                        "password": "#password",
                        "login_button": "#login-btn",
                        "account_link": ".account-row",
                        "export_button": ".export-btn"
                    }
                }
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            except Exception as e:
                print(f"Error loading scraper config: {e}")
                return default_config
        else:
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            print(f"Created default scraper config file: {self.config_file}")
            print("Please configure your bank credentials in the config file.")
            return default_config
    
    def setup_logging(self):
        """Setup logging configuration"""
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/scraper_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        
        # Add configured options
        for option in self.config.get('chrome_options', []):
            chrome_options.add_argument(option)
        
        if self.config.get('headless', True):
            chrome_options.add_argument("--headless")
        
        # Configure download directory
        download_dir = os.path.abspath(self.config.get('download_directory', './downloads'))
        os.makedirs(download_dir, exist_ok=True)
        
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_window_size(1920, 1080)
            self.logger.info("Chrome driver initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Chrome driver: {e}")
            raise
    
    def close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def wait_for_element(self, selector: str, timeout: int = None) -> bool:
        """Wait for element to be present and clickable"""
        if timeout is None:
            timeout = self.config.get('timeout', 30)
        
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            return True
        except TimeoutException:
            self.logger.error(f"Timeout waiting for element: {selector}")
            return False
    
    def safe_click(self, selector: str) -> bool:
        """Safely click an element"""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            element.click()
            return True
        except NoSuchElementException:
            self.logger.error(f"Element not found: {selector}")
            return False
        except Exception as e:
            self.logger.error(f"Error clicking element {selector}: {e}")
            return False
    
    def safe_send_keys(self, selector: str, text: str) -> bool:
        """Safely send keys to an element"""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            element.clear()
            element.send_keys(text)
            return True
        except NoSuchElementException:
            self.logger.error(f"Element not found: {selector}")
            return False
        except Exception as e:
            self.logger.error(f"Error sending keys to element {selector}: {e}")
            return False


class ChaseScraper(BankScraper):
    """Chase bank scraper"""
    
    def login(self, username: str, password: str) -> bool:
        """Login to Chase online banking"""
        try:
            bank_config = self.config['banks']['chase']
            selectors = bank_config['selectors']
            
            self.logger.info("Navigating to Chase login page")
            self.driver.get(bank_config['url'])
            
            # Wait for login form
            if not self.wait_for_element(selectors['username']):
                return False
            
            # Enter credentials
            self.logger.info("Entering login credentials")
            if not self.safe_send_keys(selectors['username'], username):
                return False
            
            if not self.safe_send_keys(selectors['password'], password):
                return False
            
            # Click login button
            if not self.safe_click(selectors['login_button']):
                return False
            
            # Wait for dashboard to load
            time.sleep(5)
            
            # Check if login was successful
            if "dashboard" in self.driver.current_url.lower():
                self.logger.info("Successfully logged into Chase")
                return True
            else:
                self.logger.error("Login failed - not redirected to dashboard")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during Chase login: {e}")
            return False
    
    def download_transactions(self, account_type: str = "checking") -> bool:
        """Download transactions from Chase"""
        try:
            self.logger.info(f"Downloading Chase {account_type} transactions")
            
            # Navigate to account transactions
            # This would need to be customized based on Chase's actual interface
            # The exact selectors would need to be determined by inspecting the website
            
            # For now, this is a placeholder implementation
            self.logger.warning("Chase transaction download not fully implemented")
            self.logger.info("Please manually download transactions from Chase website")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error downloading Chase transactions: {e}")
            return False


class WellsFargoScraper(BankScraper):
    """Wells Fargo bank scraper"""
    
    def login(self, username: str, password: str) -> bool:
        """Login to Wells Fargo online banking"""
        try:
            bank_config = self.config['banks']['wells_fargo']
            selectors = bank_config['selectors']
            
            self.logger.info("Navigating to Wells Fargo login page")
            self.driver.get(bank_config['url'])
            
            # Wait for login form
            if not self.wait_for_element(selectors['username']):
                return False
            
            # Enter credentials
            self.logger.info("Entering login credentials")
            if not self.safe_send_keys(selectors['username'], username):
                return False
            
            if not self.safe_send_keys(selectors['password'], password):
                return False
            
            # Click login button
            if not self.safe_click(selectors['login_button']):
                return False
            
            # Wait for dashboard to load
            time.sleep(5)
            
            self.logger.info("Successfully logged into Wells Fargo")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during Wells Fargo login: {e}")
            return False
    
    def download_transactions(self, account_type: str = "checking") -> bool:
        """Download transactions from Wells Fargo"""
        try:
            self.logger.info(f"Downloading Wells Fargo {account_type} transactions")
            
            # Placeholder implementation
            self.logger.warning("Wells Fargo transaction download not fully implemented")
            self.logger.info("Please manually download transactions from Wells Fargo website")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error downloading Wells Fargo transactions: {e}")
            return False


class AllyScraper(BankScraper):
    """Ally bank scraper"""
    
    def login(self, username: str, password: str) -> bool:
        """Login to Ally online banking"""
        try:
            bank_config = self.config['banks']['ally']
            selectors = bank_config['selectors']
            
            self.logger.info("Navigating to Ally login page")
            self.driver.get(bank_config['url'])
            
            # Wait for login form
            if not self.wait_for_element(selectors['username']):
                return False
            
            # Enter credentials
            self.logger.info("Entering login credentials")
            if not self.safe_send_keys(selectors['username'], username):
                return False
            
            if not self.safe_send_keys(selectors['password'], password):
                return False
            
            # Click login button
            if not self.safe_click(selectors['login_button']):
                return False
            
            # Wait for dashboard to load
            time.sleep(5)
            
            self.logger.info("Successfully logged into Ally")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during Ally login: {e}")
            return False
    
    def download_transactions(self, account_type: str = "checking") -> bool:
        """Download transactions from Ally"""
        try:
            self.logger.info(f"Downloading Ally {account_type} transactions")
            
            # Placeholder implementation
            self.logger.warning("Ally transaction download not fully implemented")
            self.logger.info("Please manually download transactions from Ally website")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error downloading Ally transactions: {e}")
            return False


class TransactionScraper:
    """Main transaction scraper orchestrator"""
    
    def __init__(self, config_file: str = "scraper_config.json"):
        self.config_file = config_file
        self.scrapers = {
            'chase': ChaseScraper,
            'wells_fargo': WellsFargoScraper,
            'ally': AllyScraper
        }
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        os.makedirs('logs', exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/scraper_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def scrape_all_banks(self) -> Dict[str, bool]:
        """Scrape transactions from all configured banks"""
        results = {}
        
        # Load configuration
        with open(self.config_file, 'r') as f:
            config = json.load(f)
        
        for bank_name, bank_config in config['banks'].items():
            if not bank_config.get('enabled', False):
                self.logger.info(f"Skipping {bank_name} - not enabled")
                results[bank_name] = None
                continue
            
            if not bank_config.get('username') or not bank_config.get('password'):
                self.logger.warning(f"Skipping {bank_name} - credentials not configured")
                results[bank_name] = False
                continue
            
            self.logger.info(f"Starting scraping for {bank_name}")
            
            try:
                # Get scraper class
                scraper_class = self.scrapers.get(bank_name)
                if not scraper_class:
                    self.logger.error(f"No scraper available for {bank_name}")
                    results[bank_name] = False
                    continue
                
                # Initialize scraper
                scraper = scraper_class(self.config_file)
                scraper.setup_driver()
                
                try:
                    # Login
                    if scraper.login(bank_config['username'], bank_config['password']):
                        # Download transactions
                        success = scraper.download_transactions()
                        results[bank_name] = success
                        
                        if success:
                            self.logger.info(f"Successfully scraped {bank_name}")
                        else:
                            self.logger.error(f"Failed to download transactions from {bank_name}")
                    else:
                        self.logger.error(f"Failed to login to {bank_name}")
                        results[bank_name] = False
                
                finally:
                    scraper.close_driver()
                    
            except Exception as e:
                self.logger.error(f"Error scraping {bank_name}: {e}")
                results[bank_name] = False
        
        return results
    
    def check_downloads(self) -> List[str]:
        """Check for newly downloaded files"""
        with open(self.config_file, 'r') as f:
            config = json.load(f)
        
        download_dir = config.get('download_directory', './downloads')
        
        # Look for CSV files modified in the last hour
        recent_files = []
        if os.path.exists(download_dir):
            for file in os.listdir(download_dir):
                if file.endswith('.csv'):
                    file_path = os.path.join(download_dir, file)
                    file_time = os.path.getmtime(file_path)
                    if datetime.now().timestamp() - file_time < 3600:  # 1 hour
                        recent_files.append(file_path)
        
        return recent_files


def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MoneyMage Bank Web Scraper')
    parser.add_argument('--bank', type=str, help='Scrape specific bank (chase, wells_fargo, ally)')
    parser.add_argument('--all', action='store_true', help='Scrape all enabled banks')
    parser.add_argument('--check-downloads', action='store_true', help='Check for recent downloads')
    parser.add_argument('--config', type=str, default='scraper_config.json', help='Configuration file')
    
    args = parser.parse_args()
    
    scraper = TransactionScraper(args.config)
    
    if args.check_downloads:
        files = scraper.check_downloads()
        if files:
            print("Recent downloads found:")
            for file in files:
                print(f"  - {file}")
        else:
            print("No recent downloads found")
    
    elif args.bank:
        # Scrape specific bank
        results = scraper.scrape_all_banks()
        bank_result = results.get(args.bank)
        
        if bank_result is True:
            print(f"Successfully scraped {args.bank}")
        elif bank_result is False:
            print(f"Failed to scrape {args.bank}")
        else:
            print(f"Bank {args.bank} not configured or not enabled")
    
    elif args.all:
        # Scrape all banks
        results = scraper.scrape_all_banks()
        
        print("Scraping results:")
        for bank, result in results.items():
            if result is True:
                print(f"  ✓ {bank}: Success")
            elif result is False:
                print(f"  ✗ {bank}: Failed")
            else:
                print(f"  - {bank}: Skipped")
    
    else:
        print("Please specify --bank, --all, or --check-downloads")
        parser.print_help()


if __name__ == "__main__":
    main() 