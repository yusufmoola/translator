"""
OAuth2 Client for Quran.Foundation API
Handles both client_credentials (Content API) and authorization_code with PKCE (User API)
"""

import hashlib
import base64
import secrets
import json
import os
import time
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, urlparse, parse_qs
from typing import Optional, Dict, Callable
import requests


class OAuth2Client:
    def __init__(self, client_id: str, client_secret: str, environment: str = "production"):
        self.client_id = client_id
        self.client_secret = client_secret

        if environment == "prelive":
            self.auth_base = "https://prelive-oauth2.quran.foundation"
            self.api_base = "https://apis-prelive.quran.foundation"
        else:
            self.auth_base = "https://oauth2.quran.foundation"
            self.api_base = "https://apis.quran.foundation"

        self.token_endpoint = f"{self.auth_base}/oauth2/token"
        self.authorize_endpoint = f"{self.auth_base}/oauth2/auth"

        self._content_token = None
        self._content_token_expires = 0
        self._user_token = None
        self._user_refresh_token = None
        self._user_token_expires = 0

        self._token_file = os.path.join(os.path.dirname(__file__), "data", ".user_token.json")
        self._load_saved_tokens()

    def _load_saved_tokens(self):
        """Load saved user tokens from disk"""
        try:
            if os.path.exists(self._token_file):
                with open(self._token_file, 'r') as f:
                    data = json.load(f)
                self._user_token = data.get("access_token")
                self._user_refresh_token = data.get("refresh_token")
                self._user_token_expires = data.get("expires_at", 0)
        except Exception:
            pass

    def _save_user_tokens(self):
        """Save user tokens to disk for persistence"""
        try:
            os.makedirs(os.path.dirname(self._token_file), exist_ok=True)
            with open(self._token_file, 'w') as f:
                json.dump({
                    "access_token": self._user_token,
                    "refresh_token": self._user_refresh_token,
                    "expires_at": self._user_token_expires
                }, f)
        except Exception:
            pass

    # --- Content API (client_credentials) ---

    def get_content_token(self) -> Optional[str]:
        """Get a valid content API token, refreshing if needed"""
        if self._content_token and time.time() < self._content_token_expires - 60:
            return self._content_token

        try:
            response = requests.post(
                self.token_endpoint,
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials", "scope": "content"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=15
            )
            response.raise_for_status()
            data = response.json()

            self._content_token = data["access_token"]
            self._content_token_expires = time.time() + data.get("expires_in", 3600)
            return self._content_token

        except Exception as e:
            print(f"Failed to get content token: {e}")
            return None

    def get_content_headers(self) -> Optional[Dict[str, str]]:
        """Get headers for Content API requests"""
        token = self.get_content_token()
        if not token:
            return None
        return {
            "x-auth-token": token,
            "x-client-id": self.client_id,
            "Accept": "application/json"
        }

    # --- User API (authorization_code + PKCE) ---

    def _generate_pkce(self) -> tuple:
        """Generate PKCE code_verifier and code_challenge"""
        code_verifier = secrets.token_urlsafe(64)[:128]
        digest = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode()
        return code_verifier, code_challenge

    def is_user_authenticated(self) -> bool:
        """Check if user has a valid (or refreshable) session"""
        if self._user_token and time.time() < self._user_token_expires - 60:
            return True
        if self._user_refresh_token:
            return self._refresh_user_token()
        return False

    def get_user_token(self) -> Optional[str]:
        """Get a valid user token, refreshing if needed"""
        if self._user_token and time.time() < self._user_token_expires - 60:
            return self._user_token
        if self._user_refresh_token:
            if self._refresh_user_token():
                return self._user_token
        return None

    def get_user_headers(self) -> Optional[Dict[str, str]]:
        """Get headers for User API requests"""
        token = self.get_user_token()
        if not token:
            return None
        return {
            "x-auth-token": token,
            "x-client-id": self.client_id,
            "Accept": "application/json"
        }

    def start_login_flow(self, redirect_port: int = 8765,
                         scopes: str = "openid offline_access bookmark collection reading_session",
                         callback: Optional[Callable[[bool], None]] = None):
        """Start the OAuth2 login flow in a background thread"""
        thread = threading.Thread(
            target=self._run_login_flow,
            args=(redirect_port, scopes, callback),
            daemon=True
        )
        thread.start()

    def _run_login_flow(self, redirect_port: int, scopes: str,
                        callback: Optional[Callable[[bool], None]]):
        """Execute the OAuth2 authorization code flow with PKCE"""
        code_verifier, code_challenge = self._generate_pkce()
        state = secrets.token_urlsafe(32)
        redirect_uri = f"http://localhost:{redirect_port}/callback"
        # Note: must exactly match registered URI at Quran.Foundation

        auth_params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": redirect_uri,
            "scope": scopes,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
            "nonce": secrets.token_urlsafe(16)
        }

        auth_url = f"{self.authorize_endpoint}?{urlencode(auth_params)}"

        received_code = {"code": None, "error": None}

        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                parsed = urlparse(self.path)
                params = parse_qs(parsed.query)
                # Handle favicon and other irrelevant requests
                if parsed.path not in ("/", "/callback"):
                    self.send_response(404)
                    self.end_headers()
                    return

                if params.get("state", [None])[0] != state:
                    received_code["error"] = "State mismatch"
                    self.send_response(400)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"<h1>Error: State mismatch</h1>")
                    return

                if "code" in params:
                    received_code["code"] = params["code"][0]
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(
                        b"<h1>Login successful!</h1>"
                        b"<p>You can close this window and return to the app.</p>"
                    )
                else:
                    received_code["error"] = params.get("error", ["unknown"])[0]
                    self.send_response(400)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"<h1>Login failed</h1>")

            def log_message(self, format, *args):
                pass

        server = HTTPServer(("localhost", redirect_port), CallbackHandler)
        server.timeout = 120

        webbrowser.open(auth_url)

        server.handle_request()
        server.server_close()

        if received_code["code"]:
            success = self._exchange_code(received_code["code"], redirect_uri, code_verifier)
            if callback:
                callback(success)
        else:
            if callback:
                callback(False)

    def _exchange_code(self, code: str, redirect_uri: str, code_verifier: str) -> bool:
        """Exchange authorization code for tokens"""
        try:
            response = requests.post(
                self.token_endpoint,
                auth=(self.client_id, self.client_secret),
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "code_verifier": code_verifier
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=15
            )
            response.raise_for_status()
            data = response.json()

            self._user_token = data["access_token"]
            self._user_refresh_token = data.get("refresh_token")
            self._user_token_expires = time.time() + data.get("expires_in", 3600)
            self._save_user_tokens()
            return True

        except Exception as e:
            print(f"Token exchange failed: {e}")
            return False

    def _refresh_user_token(self) -> bool:
        """Refresh the user access token"""
        if not self._user_refresh_token:
            return False

        try:
            response = requests.post(
                self.token_endpoint,
                auth=(self.client_id, self.client_secret),
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self._user_refresh_token
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=15
            )
            response.raise_for_status()
            data = response.json()

            self._user_token = data["access_token"]
            if "refresh_token" in data:
                self._user_refresh_token = data["refresh_token"]
            self._user_token_expires = time.time() + data.get("expires_in", 3600)
            self._save_user_tokens()
            return True

        except Exception as e:
            print(f"Token refresh failed: {e}")
            self._user_token = None
            self._user_refresh_token = None
            self._save_user_tokens()
            return False

    def logout(self):
        """Clear all user tokens"""
        self._user_token = None
        self._user_refresh_token = None
        self._user_token_expires = 0
        if os.path.exists(self._token_file):
            os.remove(self._token_file)
