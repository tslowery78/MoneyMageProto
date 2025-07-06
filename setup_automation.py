#!/usr/bin/env python3
"""
MoneyMage Automation Setup Script
This script helps set up and configure the automated transaction processing
"""

import os
import sys
import json
import subprocess
import platform
from pathlib import Path
from datetime import datetime
import getpass


class AutomationSetup:
    """Setup automation for MoneyMage"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.config_files = {
            'scheduler': 'scheduler_config.json',
            'plaid': 'plaid_config.json',
            'scraper': 'scraper_config.json'
        }
        
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        print("Checking dependencies...")
        
        required_packages = [
            'schedule',
            'requests',
            'selenium',
            'webdriver-manager'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
                print(f"✓ {package} is installed")
            except ImportError:
                missing_packages.append(package)
                print(f"✗ {package} is missing")
        
        if missing_packages:
            print(f"\nMissing packages: {', '.join(missing_packages)}")
            print("Installing missing packages...")
            
            try:
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install'
                ] + missing_packages)
                print("✓ All dependencies installed successfully")
            except subprocess.CalledProcessError:
                print("✗ Failed to install dependencies")
                print("Please manually install: pip install " + " ".join(missing_packages))
                return False
        
        return True
    
    def setup_scheduler(self):
        """Setup the transaction scheduler"""
        print("\n" + "="*50)
        print("SETTING UP TRANSACTION SCHEDULER")
        print("="*50)
        
        config_path = self.project_root / self.config_files['scheduler']
        
        if config_path.exists():
            response = input(f"Scheduler config already exists. Overwrite? (y/N): ")
            if response.lower() != 'y':
                print("Skipping scheduler setup")
                return
        
        config = {
            "budget_file": "Budget_2025.xlsx",
            "transactions_file": "transactions.xlsx",
            "budget_year": 2025,
            "schedule_time": "06:00",
            "email_notifications": False,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "email_from": "",
            "email_to": "",
            "email_password": "",
            "download_directories": {
                "macos": str(Path.home() / "Downloads"),
                "windows": str(Path.home() / "Downloads"),
                "current": "./"
            },
            "max_retries": 3,
            "retry_delay": 300,
            "backup_enabled": True,
            "log_level": "INFO"
        }
        
        print("\nConfiguring scheduler settings...")
        
        # Basic settings
        budget_year = input(f"Budget year (default: {config['budget_year']}): ").strip()
        if budget_year:
            config['budget_year'] = int(budget_year)
        
        schedule_time = input(f"Daily run time (default: {config['schedule_time']}): ").strip()
        if schedule_time:
            config['schedule_time'] = schedule_time
        
        budget_file = input(f"Budget file name (default: {config['budget_file']}): ").strip()
        if budget_file:
            config['budget_file'] = budget_file
        
        # Email notifications
        email_notifications = input("Enable email notifications? (y/N): ").strip().lower()
        if email_notifications == 'y':
            config['email_notifications'] = True
            config['email_from'] = input("From email address: ").strip()
            config['email_to'] = input("To email address: ").strip()
            config['email_password'] = getpass.getpass("Email password (for Gmail, use app password): ")
            
            smtp_server = input(f"SMTP server (default: {config['smtp_server']}): ").strip()
            if smtp_server:
                config['smtp_server'] = smtp_server
            
            smtp_port = input(f"SMTP port (default: {config['smtp_port']}): ").strip()
            if smtp_port:
                config['smtp_port'] = int(smtp_port)
        
        # Save config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✓ Scheduler configuration saved to {config_path}")
        
        # Test scheduler
        test_scheduler = input("Test scheduler now? (y/N): ").strip().lower()
        if test_scheduler == 'y':
            print("Testing scheduler...")
            try:
                from auto_transaction_scheduler import TransactionScheduler
                scheduler = TransactionScheduler(str(config_path))
                result = scheduler.run_once()
                if result:
                    print("✓ Scheduler test successful")
                else:
                    print("✗ Scheduler test failed - check logs")
            except Exception as e:
                print(f"✗ Scheduler test failed: {e}")
    
    def setup_plaid_api(self):
        """Setup Plaid API integration"""
        print("\n" + "="*50)
        print("SETTING UP PLAID API INTEGRATION")
        print("="*50)
        
        config_path = self.project_root / self.config_files['plaid']
        
        print("Plaid API Setup:")
        print("1. Go to https://plaid.com/developers/")
        print("2. Create a free account")
        print("3. Create a new app")
        print("4. Get your Client ID and Secret")
        print()
        
        setup_plaid = input("Do you want to configure Plaid API now? (y/N): ").strip().lower()
        if setup_plaid != 'y':
            print("Skipping Plaid API setup")
            return
        
        config = {
            "client_id": "",
            "secret": "",
            "environment": "sandbox",
            "products": ["transactions"],
            "country_codes": ["US"],
            "access_tokens": {},
            "account_mapping": {}
        }
        
        config['client_id'] = input("Plaid Client ID: ").strip()
        config['secret'] = getpass.getpass("Plaid Secret: ")
        
        environment = input("Environment (sandbox/development/production) [default: sandbox]: ").strip()
        if environment:
            config['environment'] = environment
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✓ Plaid configuration saved to {config_path}")
        print("\nTo connect bank accounts:")
        print("1. Run: python plaid_integration.py --setup <account_name>")
        print("2. Follow the link token instructions")
        print("3. Complete bank connection in browser")
        print("4. Save the public token")
    
    def setup_web_scraper(self):
        """Setup web scraper"""
        print("\n" + "="*50)
        print("SETTING UP WEB SCRAPER")
        print("="*50)
        
        config_path = self.project_root / self.config_files['scraper']
        
        print("Web scraper requires Chrome browser and ChromeDriver")
        print("Warning: Storing bank credentials in config files is not secure!")
        print("Consider using environment variables or a secure credential manager.")
        print()
        
        setup_scraper = input("Do you want to configure web scraper now? (y/N): ").strip().lower()
        if setup_scraper != 'y':
            print("Skipping web scraper setup")
            return
        
        # Check if Chrome is installed
        try:
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["which", "google-chrome"], check=True, capture_output=True)
            else:  # Windows/Linux
                subprocess.run(["where", "chrome"], check=True, capture_output=True)
            print("✓ Chrome browser found")
        except subprocess.CalledProcessError:
            print("✗ Chrome browser not found")
            print("Please install Chrome browser first")
            return
        
        # Install ChromeDriver
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            driver_path = ChromeDriverManager().install()
            print(f"✓ ChromeDriver installed at: {driver_path}")
        except Exception as e:
            print(f"✗ Failed to install ChromeDriver: {e}")
            return
        
        config = {
            "download_directory": str(self.project_root / "downloads"),
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
        
        # Configure banks
        for bank_name in config['banks'].keys():
            enable_bank = input(f"Enable {bank_name} scraping? (y/N): ").strip().lower()
            if enable_bank == 'y':
                config['banks'][bank_name]['enabled'] = True
                print(f"Configuring {bank_name}...")
                print("WARNING: Credentials will be stored in plain text!")
                config['banks'][bank_name]['username'] = input(f"{bank_name} username: ").strip()
                config['banks'][bank_name]['password'] = getpass.getpass(f"{bank_name} password: ")
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✓ Web scraper configuration saved to {config_path}")
        print("\nTo test web scraper:")
        print("python web_scraper.py --bank <bank_name>")
    
    def create_startup_scripts(self):
        """Create platform-specific startup scripts"""
        print("\n" + "="*50)
        print("CREATING STARTUP SCRIPTS")
        print("="*50)
        
        create_scripts = input("Create startup scripts for automatic execution? (y/N): ").strip().lower()
        if create_scripts != 'y':
            print("Skipping startup script creation")
            return
        
        system = platform.system()
        
        if system == "Darwin":  # macOS
            self.create_macos_launchd_script()
        elif system == "Windows":
            self.create_windows_task_script()
        elif system == "Linux":
            self.create_linux_cron_script()
        else:
            print(f"Unsupported platform: {system}")
    
    def create_macos_launchd_script(self):
        """Create macOS LaunchDaemon script"""
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.moneymage.scheduler</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{self.project_root}/auto_transaction_scheduler.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{self.project_root}</string>
    <key>StandardOutPath</key>
    <string>{self.project_root}/logs/scheduler.log</string>
    <key>StandardErrorPath</key>
    <string>{self.project_root}/logs/scheduler_error.log</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>"""
        
        plist_path = Path.home() / "Library/LaunchAgents/com.moneymage.scheduler.plist"
        
        with open(plist_path, 'w') as f:
            f.write(plist_content)
        
        print(f"✓ Created LaunchDaemon script: {plist_path}")
        print("To start the service:")
        print(f"launchctl load {plist_path}")
        print("To stop the service:")
        print(f"launchctl unload {plist_path}")
    
    def create_windows_task_script(self):
        """Create Windows Task Scheduler script"""
        batch_content = f"""@echo off
cd /d "{self.project_root}"
"{sys.executable}" auto_transaction_scheduler.py
"""
        
        batch_path = self.project_root / "run_scheduler.bat"
        
        with open(batch_path, 'w') as f:
            f.write(batch_content)
        
        print(f"✓ Created batch script: {batch_path}")
        print("To create a scheduled task:")
        print("1. Open Task Scheduler")
        print("2. Create Basic Task")
        print("3. Set trigger to Daily at your preferred time")
        print(f"4. Set action to start program: {batch_path}")
    
    def create_linux_cron_script(self):
        """Create Linux cron script"""
        cron_line = f"0 6 * * * cd {self.project_root} && {sys.executable} auto_transaction_scheduler.py"
        
        print("Add this line to your crontab (run 'crontab -e'):")
        print(cron_line)
        print("This will run the scheduler daily at 6:00 AM")
    
    def test_existing_setup(self):
        """Test existing automation setup"""
        print("\n" + "="*50)
        print("TESTING EXISTING SETUP")
        print("="*50)
        
        # Test scheduler
        scheduler_config = self.project_root / self.config_files['scheduler']
        if scheduler_config.exists():
            print("Testing scheduler...")
            try:
                from auto_transaction_scheduler import TransactionScheduler
                scheduler = TransactionScheduler(str(scheduler_config))
                # Don't actually run, just test initialization
                print("✓ Scheduler configuration valid")
            except Exception as e:
                print(f"✗ Scheduler test failed: {e}")
        else:
            print("✗ Scheduler not configured")
        
        # Test Plaid API
        plaid_config = self.project_root / self.config_files['plaid']
        if plaid_config.exists():
            print("Testing Plaid API...")
            try:
                from plaid_integration import PlaidTransactionFetcher
                fetcher = PlaidTransactionFetcher(str(plaid_config))
                if fetcher.config.client_id and fetcher.config.secret:
                    print("✓ Plaid API configuration valid")
                else:
                    print("✗ Plaid API credentials missing")
            except Exception as e:
                print(f"✗ Plaid API test failed: {e}")
        else:
            print("✗ Plaid API not configured")
        
        # Test web scraper
        scraper_config = self.project_root / self.config_files['scraper']
        if scraper_config.exists():
            print("Testing web scraper...")
            try:
                from web_scraper import TransactionScraper
                scraper = TransactionScraper(str(scraper_config))
                print("✓ Web scraper configuration valid")
            except Exception as e:
                print(f"✗ Web scraper test failed: {e}")
        else:
            print("✗ Web scraper not configured")
    
    def run_setup(self):
        """Run the complete setup process"""
        print("MoneyMage Automation Setup")
        print("=" * 50)
        
        # Check dependencies first
        if not self.check_dependencies():
            print("Please install dependencies before continuing")
            return
        
        # Main setup menu
        while True:
            print("\nSetup Options:")
            print("1. Setup Transaction Scheduler")
            print("2. Setup Plaid API Integration")
            print("3. Setup Web Scraper")
            print("4. Create Startup Scripts")
            print("5. Test Existing Setup")
            print("6. Exit")
            
            choice = input("\nSelect option (1-6): ").strip()
            
            if choice == '1':
                self.setup_scheduler()
            elif choice == '2':
                self.setup_plaid_api()
            elif choice == '3':
                self.setup_web_scraper()
            elif choice == '4':
                self.create_startup_scripts()
            elif choice == '5':
                self.test_existing_setup()
            elif choice == '6':
                print("Setup complete!")
                break
            else:
                print("Invalid option. Please select 1-6.")


def main():
    """Main function"""
    setup = AutomationSetup()
    setup.run_setup()


if __name__ == "__main__":
    main() 