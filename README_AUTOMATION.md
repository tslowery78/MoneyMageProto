# MoneyMage Automation Features

This document explains the new automation features added to MoneyMage that allow you to automatically fetch and process transactions from your bank accounts.

## Overview

The automation system provides three different approaches to getting your transactions automatically:

1. **Transaction Scheduler** - Automates the existing CSV processing workflow
2. **Plaid API Integration** - Directly fetches transactions from banks using APIs
3. **Web Scraper** - Automatically downloads CSV files from bank websites

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the setup script:**
   ```bash
   python setup_automation.py
   ```

3. **Choose your automation method and follow the guided setup**

## Automation Methods

### 1. Transaction Scheduler

The simplest automation that works with your existing workflow. It automatically processes any new CSV files you download from your banks and runs your budget processing daily.

**Features:**
- Daily automated processing at your chosen time
- Email notifications of results
- Automatic backup creation
- Retry logic for failed runs
- Comprehensive logging

**Setup:**
```bash
python setup_automation.py
# Choose option 1: Setup Transaction Scheduler
```

**Manual setup:**
1. Copy `scheduler_config.json.example` to `scheduler_config.json`
2. Configure your settings
3. Run: `python auto_transaction_scheduler.py --run-once` (test)
4. Run: `python auto_transaction_scheduler.py` (start scheduler)

**Usage:**
```bash
# Test run once
python auto_transaction_scheduler.py --run-once

# Start daily scheduler
python auto_transaction_scheduler.py

# Send test notification
python auto_transaction_scheduler.py --test-notification
```

### 2. Plaid API Integration

The most robust solution that directly connects to your bank accounts via secure APIs. No need to manually download CSV files.

**Features:**
- Direct connection to 11,000+ financial institutions
- Automatic transaction categorization
- Real-time balance checking
- Secure authentication
- No manual CSV downloads needed

**Requirements:**
- Plaid developer account (free for development)
- Bank account that supports Plaid

**Setup:**
1. Create account at [Plaid.com/developers](https://plaid.com/developers/)
2. Get your Client ID and Secret
3. Run setup: `python setup_automation.py` → option 2
4. Connect your accounts:
   ```bash
   # Setup bank connection
   python plaid_integration.py --setup "my_checking"
   
   # Save the public token after bank authorization
   python plaid_integration.py --save-token "my_checking" "public-token-from-browser"
   ```

**Usage:**
```bash
# Fetch last 30 days of transactions
python plaid_integration.py --fetch 30

# List configured accounts
python plaid_integration.py --list-accounts
```

### 3. Web Scraper

Automatically logs into your bank websites and downloads CSV files. Use as a backup when APIs aren't available.

**⚠️ Security Warning:** This method stores your banking credentials in config files. Use with caution and ensure your computer is secure.

**Features:**
- Automated login and CSV download
- Support for major banks (Chase, Wells Fargo, Ally)
- Headless browser operation
- Configurable selectors for different banks

**Requirements:**
- Chrome browser
- Bank accounts with web access

**Setup:**
```bash
python setup_automation.py
# Choose option 3: Setup Web Scraper
```

**Usage:**
```bash
# Scrape all configured banks
python web_scraper.py --all

# Scrape specific bank
python web_scraper.py --bank chase

# Check for recent downloads
python web_scraper.py --check-downloads
```

## Configuration Files

### scheduler_config.json
```json
{
  "budget_file": "Budget_2025.xlsx",
  "transactions_file": "transactions.xlsx",
  "budget_year": 2025,
  "schedule_time": "06:00",
  "email_notifications": true,
  "email_from": "your-email@gmail.com",
  "email_to": "your-email@gmail.com",
  "email_password": "your-app-password"
}
```

### plaid_config.json
```json
{
  "client_id": "your-plaid-client-id",
  "secret": "your-plaid-secret",
  "environment": "sandbox",
  "access_tokens": {
    "my_checking": "access-token-here"
  }
}
```

### scraper_config.json
```json
{
  "banks": {
    "chase": {
      "enabled": true,
      "username": "your-username",
      "password": "your-password"
    }
  }
}
```

## System Integration

### Running as a Service

#### macOS (LaunchDaemon)
The setup script creates a LaunchDaemon that runs the scheduler automatically:
```bash
# Load the service
launchctl load ~/Library/LaunchAgents/com.moneymage.scheduler.plist

# Unload the service
launchctl unload ~/Library/LaunchAgents/com.moneymage.scheduler.plist
```

#### Windows (Task Scheduler)
1. Run setup script to create batch file
2. Open Task Scheduler
3. Create Basic Task
4. Set trigger to Daily
5. Set action to run the generated batch file

#### Linux (Cron)
Add this line to your crontab (`crontab -e`):
```
0 6 * * * cd /path/to/MoneyMageProto && python auto_transaction_scheduler.py
```

## Combining Methods

You can use multiple methods together for maximum reliability:

1. **Primary:** Plaid API for supported banks
2. **Backup:** Web scraper for unsupported banks
3. **Fallback:** Manual CSV + Scheduler for any issues

Example workflow:
```bash
# Morning: Automatic Plaid fetch
python plaid_integration.py --fetch 7

# If that fails, try web scraper
python web_scraper.py --all

# Scheduler processes everything automatically
```

## Troubleshooting

### Common Issues

**"No transactions found"**
- Check if CSV files are in the correct download directory
- Verify file naming patterns match expectations
- Check logs in `logs/` directory

**"Email notifications not working"**
- For Gmail, use App Passwords instead of your regular password
- Check SMTP settings in config
- Test with: `python auto_transaction_scheduler.py --test-notification`

**"Plaid API errors"**
- Verify Client ID and Secret are correct
- Check environment setting (sandbox/development/production)
- Ensure bank account is supported

**"Web scraper login fails"**
- Bank websites change frequently - selectors may need updates
- Some banks have anti-automation measures
- Try running in non-headless mode for debugging

### Logging

All automation scripts create detailed logs in the `logs/` directory:
- `scheduler_YYYYMMDD.log` - Scheduler operations
- `plaid_YYYYMMDD.log` - Plaid API calls
- `scraper_YYYYMMDD.log` - Web scraper activities

### Security Best Practices

1. **Use secure credentials storage:**
   - Environment variables instead of config files
   - Operating system credential managers
   - Encrypted configuration files

2. **Limit access:**
   - Set restrictive file permissions on config files
   - Use dedicated email accounts for notifications
   - Regularly rotate passwords and API keys

3. **Monitor activity:**
   - Review logs regularly
   - Set up alerts for failed authentications
   - Monitor your bank accounts for unusual activity

## Integration with Existing Workflow

The automation features are designed to work with your existing MoneyMage setup:

1. **CSV Processing:** All methods ultimately feed into your existing `transactions.py` processing
2. **Auto-categorization:** Your `auto_categories.xlsx` rules still apply
3. **Budget Integration:** Processed transactions update your budget as before
4. **Backup System:** Archives are still created automatically

## Support and Development

### Adding New Banks

For **Web Scraper:**
1. Create new scraper class inheriting from `BankScraper`
2. Implement `login()` and `download_transactions()` methods
3. Add bank configuration to default config
4. Test thoroughly with your account

For **Plaid API:**
- Most banks are already supported through Plaid
- Check [Plaid's institution list](https://plaid.com/docs/institutions/)

### Customization

All scripts are designed to be easily customizable:
- Modify scheduling times and retry logic
- Add custom notification methods (SMS, Slack, etc.)
- Integrate with other financial tools
- Add support for additional file formats

### Contributing

If you add support for new banks or improve existing features, consider contributing back to the project!

## Frequently Asked Questions

**Q: Is it safe to store my banking credentials?**
A: The web scraper method does store credentials in plain text, which has security risks. Consider using Plaid API for better security, or implement additional encryption for credential storage.

**Q: How much does Plaid cost?**
A: Plaid offers a free development tier. Production usage has costs, but for personal finance tracking, the development tier is usually sufficient.

**Q: Can I use this with banks outside the US?**
A: Plaid supports some international banks. Web scraper can be customized for any bank website. Check Plaid's supported countries list.

**Q: What if my bank changes their website?**
A: Web scraper selectors may need updates. Check logs for errors and update the selectors in the config file. Consider switching to Plaid API for more stability.

**Q: Can I run this on a server?**
A: Yes! The scheduler is designed to run on servers. For web scraper, you'll need a display server or virtual display.

## Example Complete Setup

Here's a complete setup example for someone with Chase and Ally accounts:

1. **Install and setup:**
   ```bash
   pip install -r requirements.txt
   python setup_automation.py
   ```

2. **Configure Plaid for Chase (supported):**
   - Setup Plaid account
   - Connect Chase account via Plaid

3. **Configure Web Scraper for Ally (backup):**
   - Enable Ally in scraper config
   - Add credentials (securely)

4. **Setup Scheduler:**
   - Configure daily 6 AM runs
   - Enable email notifications
   - Test the setup

5. **Create system service:**
   - Use setup script to create platform-specific service
   - Start the service

6. **Monitor:**
   - Check logs daily for first week
   - Verify transactions are being processed
   - Adjust settings as needed

This gives you a robust, automated system that fetches transactions from all your accounts and processes them daily! 