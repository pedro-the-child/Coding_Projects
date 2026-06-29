"""
Oura OAuth2 token management.
Tokens are stored in .tokens.json (gitignored) at the project root.
Refresh tokens are single-use — every refresh persists the new token immediately.
"""
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN_URL = "https://api.ouraring.com/oauth/token"
TOKEN_FILE = Path(__file__).parent.parent / ".tokens.json"

CLIENT_ID = os.environ["OURA_CLIENT_ID"]
CLIENT_SECRET = os.environ["OURA_CLIENT_SECRET"]
REDIRECT_URI = "http://localhost:8080/callback"


def _save_tokens(tokens: dict) -> None:
    TOKEN_FILE.write_text(json.dumps(tokens, indent=2))


def _load_tokens() -> dict:
    if not TOKEN_FILE.exists():
        raise FileNotFoundError(
            f"No token file found at {TOKEN_FILE}. "
            "Run exchange_code_for_tokens() first."
        )
    return json.loads(TOKEN_FILE.read_text())


def exchange_code_for_tokens(code: str) -> dict:
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
    )
    resp.raise_for_status()
    tokens = resp.json()
    tokens["obtained_at"] = time.time()
    _save_tokens(tokens)
    print(f"Tokens saved to {TOKEN_FILE}")
    return tokens


def refresh_access_token(refresh_token: str) -> dict:
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
    )
    resp.raise_for_status()
    tokens = resp.json()
    tokens["obtained_at"] = time.time()
    _save_tokens(tokens)
    return tokens


def get_valid_access_token() -> str:
    tokens = _load_tokens()
    expires_in = tokens.get("expires_in", 86400)
    obtained_at = tokens.get("obtained_at", 0)
    # Refresh if within 5 minutes of expiry
    if time.time() > obtained_at + expires_in - 300:
        print("Access token expiring soon, refreshing...")
        tokens = refresh_access_token(tokens["refresh_token"])
    return tokens["access_token"]


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 3 and sys.argv[1] == "exchange":
        code = sys.argv[2]
        result = exchange_code_for_tokens(code)
        print(f"Access token obtained. Expires in {result.get('expires_in')}s.")
    elif len(sys.argv) == 1:
        token = get_valid_access_token()
        print(f"Valid access token: {token[:10]}...")
    else:
        print("Usage: python oauth_token_store.py exchange <code>")
        print("       python oauth_token_store.py")
