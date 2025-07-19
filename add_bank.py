import os
import json
import requests
import argparse

# Configuration
CONFIG_FILE = "plaid_config.json"

def load_config():
    """Load Plaid configuration from JSON file."""
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: Configuration file '{CONFIG_FILE}' not found.")
        print("Please ensure the file exists and contains your Plaid credentials.")
        return None
    
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def get_headers(config):
    """Get common headers for Plaid API requests."""
    return {
        "Content-Type": "application/json",
        "PLAID-CLIENT-ID": config["client_id"],
        "PLAID-SECRET": config["secret"]
    }

def create_link_token(config, base_url):
    """Create a link token for Plaid Link initialization."""
    request_data = {
        "client_name": "MoneyMage",
        "products": config.get("products", ["transactions"]),
        "country_codes": config.get("country_codes", ["US"]),
        "language": "en",
        "user": {"client_user_id": "default_user"}
    }
    
    # Only add redirect_uri for sandbox environment
    if config.get("environment") == "sandbox":
        request_data["redirect_uri"] = "http://localhost:8000/"
    
    try:
        response = requests.post(
            f"{base_url}/link/token/create",
            json=request_data,
            headers=get_headers(config)
        )
        response.raise_for_status()
        return response.json().get("link_token")
    except requests.exceptions.RequestException as e:
        print(f"Error creating link token: {e}")
        print(f"Response: {e.response.text}")
        return None

def exchange_public_token(config, base_url, public_token):
    """Exchange public token for access token."""
    request_data = {"public_token": public_token}
    
    try:
        response = requests.post(
            f"{base_url}/item/public_token/exchange",
            json=request_data,
            headers=get_headers(config)
        )
        response.raise_for_status()
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"Error exchanging public token: {e}")
        return None

def save_access_token(config, account_name, access_token):
    """Save access token to the configuration file."""
    if "access_tokens" not in config:
        config["access_tokens"] = {}
    config["access_tokens"][account_name] = access_token
    
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"\nSuccessfully saved access token for '{account_name}' to {CONFIG_FILE}")
        return True
    except IOError as e:
        print(f"Error writing to config file: {e}")
        return False

def main():
    """Main entry point to add a new bank."""
    config = load_config()
    if not config:
        return

    # Determine Plaid environment and base URL
    env = config.get("environment", "sandbox")
    base_urls = {
        "sandbox": "https://sandbox.plaid.com",
        "development": "https://development.plaid.com",
        "production": "https://production.plaid.com"
    }
    base_url = base_urls.get(env, "https://sandbox.plaid.com")
    print(f"Running in {env.upper()} environment.")

    # Get account name from user
    account_name = input("--> Enter a friendly name for this bank account (e.g., 'My Checking'): ").strip()
    if not account_name:
        print("Account name cannot be empty. Aborting.")
        return

    # Create and display link token
    link_token = create_link_token(config, base_url)
    if not link_token:
        return

    print("\n" + "="*50)
    print("A link token has been created. Please complete the next steps:")
    print(f"  1. Open 'plaid_link.html' in your web browser.")
    print(f"  2. Paste the following link_token when prompted:")
    print(f"\n     {link_token}\n")
    print(f"  3. Follow the on-screen instructions to connect your account.")
    print(f"  4. When you receive a 'public_token', paste it below.")
    print("="*50 + "\n")

    # Get public token from user
    public_token = input("--> Paste the public_token here and press Enter: ").strip()
    if not public_token:
        print("No public_token provided. Aborting.")
        return

    # Exchange for access token and save
    access_token = exchange_public_token(config, base_url, public_token)
    if access_token:
        save_access_token(config, account_name, access_token)

if __name__ == "__main__":
    main() 