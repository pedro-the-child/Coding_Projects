"""
One-shot local server that captures the OAuth2 callback and exchanges the code immediately.
Run this, then visit the authorization URL in your browser.
"""
import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN_URL = "https://api.ouraring.com/oauth/token"
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "..", ".tokens.json")
CLIENT_ID = os.environ["OURA_CLIENT_ID"]
CLIENT_SECRET = os.environ["OURA_CLIENT_SECRET"]
REDIRECT_URI = "http://localhost:8080/callback"

AUTH_URL = (
    f"https://cloud.ouraring.com/oauth/authorize"
    f"?response_type=code"
    f"&client_id={CLIENT_ID}"
    f"&redirect_uri=http%3A%2F%2Flocalhost%3A8080%2Fcallback"
    f"&scope=daily+heartrate+workout+session+spo2+personal+ring_configuration"
)


class CallbackHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress default request logging

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/callback":
            self.send_response(404)
            self.end_headers()
            return

        params = parse_qs(parsed.query)
        if "error" in params:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"Error: {params['error']}".encode())
            self.server.token_result = None
            return

        code = params.get("code", [None])[0]
        if not code:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"No code in callback")
            return

        print(f"\nCode received. Exchanging for tokens...")
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

        if resp.status_code == 200:
            tokens = resp.json()
            tokens["obtained_at"] = time.time()
            with open(TOKEN_FILE, "w") as f:
                json.dump(tokens, f, indent=2)
            print(f"Tokens saved to .tokens.json")
            print(f"Access token expires in: {tokens.get('expires_in')}s")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"<h2>Success! Tokens saved. You can close this tab.</h2>")
            self.server.token_result = tokens
        else:
            print(f"Token exchange failed: {resp.status_code} {resp.text}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f"Token exchange failed: {resp.text}".encode())
            self.server.token_result = None


def run():
    print(f"\nOpen this URL in your browser:\n\n{AUTH_URL}\n")
    print("Waiting for OAuth callback on http://localhost:8080/callback ...")
    server = HTTPServer(("localhost", 8080), CallbackHandler)
    server.token_result = None
    server.handle_request()  # handle exactly one request then exit
    return server.token_result


if __name__ == "__main__":
    result = run()
    if result:
        print("\nOAuth2 setup complete.")
    else:
        print("\nOAuth2 setup failed.")
        exit(1)
