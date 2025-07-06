#!/usr/bin/env python3
"""
Automated Transaction Scheduler for MoneyMage
This script automates the daily processing of bank transactions
"""

import os
import sys
import time
import logging
import schedule
import argparse
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import json
import subprocess
from pathlib import Path

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from BudgetMeeting import BudgetMeeting
from transactions import get_new_transactions, get_old_transactions


class TransactionScheduler:
    def __init__(self, config_file="scheduler_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.setup_logging()
        
    def load_config(self):
        """Load configuration from JSON file"""
        default_config = {
            "budget_file": "Budget_2025.xlsx",
            "transactions_file": "transactions.xlsx",
            "budget_year": 2025,
            "schedule_time": "06:00",  # 6 AM daily
            "email_notifications": False,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "email_from": "",
            "email_to": "",
            "email_password": "",
            "download_directories": {
                "macos": "/Users/tslowery/Downloads/",
                "windows": "C:\\Users\\tslow\\Downloads\\",
                "current": "./"
            },
            "max_retries": 3,
            "retry_delay": 300,  # 5 minutes
            "backup_enabled": True,
            "log_level": "INFO"
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
                print(f"Error loading config: {e}")
                return default_config
        else:
            # Create default config file
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            print(f"Created default config file: {self.config_file}")
            return default_config
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.config.get('log_level', 'INFO'))
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/scheduler_{datetime.now().strftime("%Y%m%d")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def send_notification(self, subject, message, is_error=False):
        """Send email notification if configured"""
        if not self.config.get('email_notifications', False):
            return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config['email_from']
            msg['To'] = self.config['email_to']
            msg['Subject'] = f"MoneyMage: {subject}"
            
            # Add timestamp and error indicator
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "ERROR" if is_error else "SUCCESS"
            
            body = f"""
MoneyMage Automated Transaction Processing Report
Time: {timestamp}
Status: {status}

{message}

---
This is an automated message from MoneyMage Transaction Scheduler.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            server.starttls()
            server.login(self.config['email_from'], self.config['email_password'])
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"Notification sent: {subject}")
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
    
    def check_for_new_csv_files(self):
        """Check if there are new CSV files to process"""
        download_dirs = self.config['download_directories']
        
        # Determine which directory to check
        import platform
        if platform.system() == 'Darwin':
            download_dir = download_dirs.get('macos', download_dirs['current'])
        else:
            download_dir = download_dirs.get('windows', download_dirs['current'])
        
        # Check for common bank CSV patterns
        csv_patterns = [
            'CreditCard*.csv',
            'Chase3376_Activity_*.CSV',
            'Chase9*_Activity_*.csv',
            'transactions*.csv'
        ]
        
        import glob
        found_files = []
        for pattern in csv_patterns:
            files = glob.glob(os.path.join(download_dir, pattern))
            if files:
                # Check if files are newer than 24 hours
                for file in files:
                    file_time = os.path.getmtime(file)
                    if datetime.now().timestamp() - file_time < 86400:  # 24 hours
                        found_files.append(file)
        
        return found_files
    
    def process_transactions(self):
        """Main transaction processing function"""
        self.logger.info("Starting automated transaction processing...")
        
        try:
            # Check for new CSV files
            new_files = self.check_for_new_csv_files()
            if new_files:
                self.logger.info(f"Found {len(new_files)} new CSV files: {new_files}")
            else:
                self.logger.info("No new CSV files found in the last 24 hours")
            
            # Get current transaction count before processing
            _, old_transactions = get_old_transactions(self.config['transactions_file'])
            old_count = len(old_transactions.get('Date', []))
            
            # Run the budget meeting process
            BudgetMeeting(
                self.config['budget_file'],
                self.config['transactions_file'],
                self.config['budget_year']
            )
            
            # Get new transaction count after processing
            _, new_transactions = get_old_transactions(self.config['transactions_file'])
            new_count = len(new_transactions.get('Date', []))
            
            added_transactions = new_count - old_count
            
            # Send success notification
            if added_transactions > 0:
                message = f"Successfully processed {added_transactions} new transactions."
                if new_files:
                    message += f"\nProcessed files: {', '.join(os.path.basename(f) for f in new_files)}"
                self.send_notification("Transaction Processing Complete", message)
                self.logger.info(f"Successfully added {added_transactions} new transactions")
            else:
                message = "No new transactions found to process."
                self.send_notification("Transaction Processing Complete", message)
                self.logger.info("No new transactions to process")
            
            return True
            
        except Exception as e:
            error_msg = f"Error during transaction processing: {str(e)}"
            self.logger.error(error_msg)
            self.send_notification("Transaction Processing Failed", error_msg, is_error=True)
            return False
    
    def run_with_retry(self):
        """Run transaction processing with retry logic"""
        max_retries = self.config.get('max_retries', 3)
        retry_delay = self.config.get('retry_delay', 300)
        
        for attempt in range(max_retries):
            try:
                if self.process_transactions():
                    return True
                else:
                    if attempt < max_retries - 1:
                        self.logger.warning(f"Attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
                    else:
                        self.logger.error("All retry attempts failed")
                        return False
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed with exception: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    return False
        
        return False
    
    def start_scheduler(self):
        """Start the scheduled task"""
        schedule_time = self.config.get('schedule_time', '06:00')
        
        # Schedule the daily task
        schedule.every().day.at(schedule_time).do(self.run_with_retry)
        
        self.logger.info(f"Transaction scheduler started. Will run daily at {schedule_time}")
        self.send_notification("Scheduler Started", f"Transaction processing scheduled for daily at {schedule_time}")
        
        # Keep the scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def run_once(self):
        """Run transaction processing once (for testing)"""
        self.logger.info("Running transaction processing once...")
        return self.run_with_retry()


def main():
    parser = argparse.ArgumentParser(description='MoneyMage Automated Transaction Scheduler')
    parser.add_argument('--config', '-c', default='scheduler_config.json',
                        help='Configuration file path')
    parser.add_argument('--run-once', '-r', action='store_true',
                        help='Run once instead of scheduling')
    parser.add_argument('--test-notification', '-t', action='store_true',
                        help='Send test notification')
    
    args = parser.parse_args()
    
    scheduler = TransactionScheduler(args.config)
    
    if args.test_notification:
        scheduler.send_notification("Test Notification", "This is a test notification from MoneyMage scheduler.")
        print("Test notification sent (if configured)")
        return
    
    if args.run_once:
        success = scheduler.run_once()
        sys.exit(0 if success else 1)
    else:
        try:
            scheduler.start_scheduler()
        except KeyboardInterrupt:
            scheduler.logger.info("Scheduler stopped by user")
            scheduler.send_notification("Scheduler Stopped", "Transaction scheduler has been stopped manually.")


if __name__ == "__main__":
    main() 