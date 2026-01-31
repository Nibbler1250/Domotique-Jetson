#!/usr/bin/env python3
"""
Gmail OAuth2 Authentication Script
Run this locally to generate token.json, then copy to Jetson

Usage:
  1. pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
  2. python3 gmail_auth.py
  3. scp token.json simon@192.168.1.118:/home/simon/gmail_sorter/
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/gmail.labels',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events'
]

# Credentials from Jetson
CREDENTIALS = {
    "installed": {
        "client_id": "1090331470022-8smqpg6n6c0gnmpigrohe0u0nhl5dt9k.apps.googleusercontent.com",
        "project_id": "gmail-invoice-sorter",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": "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",
        "redirect_uris": ["http://localhost"]
    }
}

def authenticate():
    # Create temp credentials file
    creds_file = '/tmp/gmail_credentials.json'
    with open(creds_file, 'w') as f:
        json.dump(CREDENTIALS, f)

    print("🔐 Starting OAuth2 flow...")
    print("A browser window will open. Log in with your Gmail account.")
    print()

    flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
    creds = flow.run_local_server(port=8080)

    # Save token
    token_file = 'token.json'
    with open(token_file, 'w') as f:
        f.write(creds.to_json())

    print()
    print("✅ Authentication successful!")
    print(f"📄 Token saved to: {os.path.abspath(token_file)}")
    print()
    print("Next step - copy to Jetson:")
    print(f"  scp {token_file} simon@192.168.1.118:/home/simon/gmail_sorter/")

    # Cleanup
    os.remove(creds_file)

    return creds

if __name__ == '__main__':
    authenticate()
