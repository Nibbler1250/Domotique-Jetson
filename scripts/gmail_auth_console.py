#!/usr/bin/env python3
"""
Gmail OAuth2 Authentication Script (Console Mode)
Prints URL for manual authentication in browser

Usage:
  1. python3 gmail_auth_console.py
  2. Open the URL in your browser
  3. Paste the authorization code back
  4. scp token.json simon@192.168.1.118:/home/simon/gmail_sorter/
"""

import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.labels',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events'
]

CREDENTIALS = {
    "installed": {
        "client_id": "1090331470022-8smqpg6n6c0gnmpigrohe0u0nhl5dt9k.apps.googleusercontent.com",
        "project_id": "gmail-invoice-sorter",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "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",
        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
    }
}

def authenticate():
    # Create temp credentials file
    creds_file = '/tmp/gmail_credentials.json'
    with open(creds_file, 'w') as f:
        json.dump(CREDENTIALS, f)

    print("🔐 Gmail OAuth2 Authentication")
    print("=" * 50)
    print()

    flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)

    # Use console mode instead of browser
    creds = flow.run_local_server(
        port=8080,
        open_browser=True,
        success_message="✅ Authentification réussie! Tu peux fermer cette fenêtre."
    )

    # Save token
    token_file = 'token.json'
    with open(token_file, 'w') as f:
        f.write(creds.to_json())

    print()
    print("✅ Authentication successful!")
    print(f"📄 Token saved to: token.json")
    print()
    print("=" * 50)
    print("NEXT STEP - Copy to Jetson:")
    print()
    print(f"  scp token.json simon@192.168.1.118:/home/simon/gmail_sorter/")
    print()
    print("Then test the sorter:")
    print("  ssh simon@192.168.1.118 'cd /home/simon/gmail_sorter && python3 gmail_invoice_sorter_v2.py'")

    import os
    os.remove(creds_file)

    return creds

if __name__ == '__main__':
    authenticate()
