"""
Gmail OAuth2 Setup - Official Method.

This script helps you add the gmail.send scope to your existing authentication.
Uses Google's official OAuth2 flow - safe and compliant.
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from pathlib import Path

# IMPORTANT: Both scopes needed - readonly for watching, send for replies
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

def setup_gmail_auth():
    """
    Set up Gmail authentication with send permissions.

    This uses Google's official OAuth2 flow:
    1. Opens browser for consent
    2. User authorizes the app
    3. Saves credentials securely to gmail_token.json

    This is the OFFICIAL method recommended by Google.
    """

    print("=" * 60)
    print("Gmail OAuth2 Setup - Official Method")
    print("=" * 60)
    print()

    # Check for credentials file
    creds_file = 'client_secret_992661557953-sjj1qb7g8cf18ng35g4hrrs8egq3oekp.apps.googleusercontent.com.json'

    if not os.path.exists(creds_file):
        print("[ERROR] Credentials file not found!")
        print()
        print("Expected file:", creds_file)
        print()
        print("This file should contain your OAuth2 client credentials from")
        print("Google Cloud Console.")
        print()
        return False

    # Check existing token
    token_file = 'gmail_token.json'
    existing_creds = None

    if os.path.exists(token_file):
        print("[INFO] Found existing gmail_token.json")
        with open(token_file, 'r') as f:
            token_data = json.load(f)
            current_scopes = token_data.get('scopes', [])
            print(f"[INFO] Current scopes: {current_scopes}")

            if 'https://www.googleapis.com/auth/gmail.send' in current_scopes:
                print("[OK] You already have send permission!")
                print()
                return True

            print("[INFO] Need to add gmail.send scope")
            print()

    # Run OAuth flow to get new token with both scopes
    print("=" * 60)
    print("Starting OAuth2 Flow")
    print("=" * 60)
    print()
    print("This will:")
    print("1. Open your browser")
    print("2. Ask you to sign in to Google")
    print("3. Show permission request for:")
    print("   - Read emails (for monitoring)")
    print("   - Send emails (for replies)")
    print()
    print("This is SAFE and uses Google's official OAuth2 method.")
    print("You can revoke access anytime from your Google Account settings.")
    print()

    input("Press Enter to continue or Ctrl+C to cancel...")
    print()

    try:
        # Create flow
        flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)

        # Run local server for OAuth callback
        print("[INFO] Starting local OAuth server...")
        print("[INFO] If browser doesn't open, copy the URL from terminal")
        print()

        creds = flow.run_local_server(port=0)

        # Save credentials
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

        print()
        print("[OK] Authentication successful!")
        print(f"[OK] Token saved to {token_file}")
        print()
        print("Scopes granted:")
        for scope in creds.scopes:
            print(f"  ✓ {scope}")
        print()
        print("[SUCCESS] You can now send emails via Gmail API")
        print()

        return True

    except Exception as e:
        print(f"[ERROR] Authentication failed: {e}")
        print()
        return False

if __name__ == "__main__":
    print()
    success = setup_gmail_auth()
    print()

    if success:
        print("=" * 60)
        print("Next Steps:")
        print("=" * 60)
        print()
        print("1. Your credentials are ready")
        print("2. Restart the Brain: python -m src.orchestration.orchestrator")
        print("3. Test email send from dashboard")
        print()
        print("Email sending will now work properly via official Gmail API!")
        print()
    else:
        print("Setup incomplete. Please fix the errors above and try again.")
        print()
