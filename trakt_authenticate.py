#!/usr/bin/env python3
"""
Trakt Authentication Helper
This script helps you authenticate with Trakt and get your access token.
"""

import requests
import webbrowser
import os
from urllib.parse import urlencode

REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"  # For PIN-based auth
BASE_URL = "https://api.trakt.tv"
AUTH_URL = "https://trakt.tv/oauth/authorize"
TOKEN_URL = f"{BASE_URL}/oauth/token"
CREDENTIALS_FILE = "trakt_credentials.txt"


def load_client_credentials():
    """Load CLIENT_ID and CLIENT_SECRET from credentials file."""
    credentials = {}

    if not os.path.exists(CREDENTIALS_FILE):
        return None, None

    with open(CREDENTIALS_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                credentials[key.strip()] = value.strip()

    client_id = credentials.get('CLIENT_ID', '')
    client_secret = credentials.get('CLIENT_SECRET', '')

    if client_id.startswith('YOUR_') or client_secret.startswith('YOUR_'):
        return None, None

    return client_id, client_secret


def save_credentials(client_id, client_secret, access_token, username):
    """Save credentials to file."""
    content = f"""# Trakt API Credentials
# Generated on {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

CLIENT_ID={client_id}
CLIENT_SECRET={client_secret}
ACCESS_TOKEN={access_token}
USERNAME={username}
"""

    with open(CREDENTIALS_FILE, 'w') as f:
        f.write(content)

    print(f"✅ Credentials saved to: {CREDENTIALS_FILE}")


def get_username(access_token, client_id):
    """Fetch username using the access token."""
    headers = {
        "Content-Type": "application/json",
        "trakt-api-version": "2",
        "trakt-api-key": client_id,
        "Authorization": f"Bearer {access_token}"
    }

    try:
        response = requests.get(f"{BASE_URL}/users/settings", headers=headers)
        response.raise_for_status()
        return response.json()['user']['username']
    except:
        return None


def get_auth_url(client_id):
    """Generate the authorization URL."""
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def get_access_token(auth_code, client_id, client_secret):
    """Exchange authorization code for access token."""
    payload = {
        "code": auth_code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    response = requests.post(TOKEN_URL, json=payload)
    response.raise_for_status()

    return response.json()


def main():
    """Main authentication flow."""
    print("=" * 60)
    print("Trakt Authentication Helper")
    print("=" * 60)
    print()

    # Try to load existing credentials
    client_id, client_secret = load_client_credentials()

    if not client_id or not client_secret:
        print("⚠️  Client credentials not found or incomplete.")
        print()
        print("Steps to get credentials:")
        print("1. Go to: https://trakt.tv/oauth/applications")
        print("2. Click 'New Application'")
        print("3. Fill in the form:")
        print("   - Name: My Trakt Script (or any name)")
        print("   - Redirect uri: urn:ietf:wg:oauth:2.0:oob")
        print("4. Click 'Save App'")
        print()

        client_id = input("Enter your Client ID: ").strip()
        client_secret = input("Enter your Client Secret: ").strip()

        if not client_id or not client_secret:
            print("\n❌ Invalid credentials. Exiting.")
            return
    else:
        print(f"✓ Found existing client credentials")
        print()

    # Generate authorization URL
    auth_url = get_auth_url(client_id)

    print("Step 1: Authorize the application")
    print("-" * 60)
    print()
    print("Opening browser to authorize...")
    print("If the browser doesn't open, copy this URL:")
    print(f"\n{auth_url}\n")

    try:
        webbrowser.open(auth_url)
    except:
        pass

    print()
    auth_code = input("Paste the authorization code you received: ").strip()

    if not auth_code:
        print("\n❌ No code provided. Exiting.")
        return

    print()
    print("Step 2: Getting access token...")
    print("-" * 60)

    try:
        tokens = get_access_token(auth_code, client_id, client_secret)
        access_token = tokens['access_token']

        # Fetch username
        print("Step 3: Fetching username...")
        username = get_username(access_token, client_id)

        if not username:
            username = input("\nCouldn't fetch username automatically. Enter your Trakt username: ").strip()

        print()
        print("✅ Success! Authentication complete.")
        print("=" * 60)
        print(f"Username: {username}")
        print(f"Access Token: {access_token[:20]}...")
        print(f"Expires In: {tokens['expires_in']} seconds (~{tokens['expires_in']//86400} days)")
        print("=" * 60)
        print()

        # Save credentials
        save_credentials(client_id, client_secret, access_token, username)

        print()
        print("⚠️  Keep this file secure! Add it to .gitignore if using git.")
        print()
        print("You can now run: python trakt_gap_filler.py")

    except requests.exceptions.HTTPError as e:
        print(f"\n❌ Error getting access token: {e}")
        if hasattr(e, 'response'):
            print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
