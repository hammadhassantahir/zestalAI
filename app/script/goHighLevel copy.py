# gohighlevel.py
import requests
import time

class GoHighLevelAPI:
    BASE_URL = "https://rest.gohighlevel.com/v1"

    def __init__(self, client_id, client_secret, redirect_uri, refresh_token=None, access_token=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.token_expiry = None  # epoch timestamp

    def get_access_token(self, code):
        """Exchange authorization code for access/refresh tokens"""
        url = "https://services.leadconnectorhq.com/oauth/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
        }
        r = requests.post(url, data=payload)
        r.raise_for_status()
        data = r.json()
        self._store_tokens(data)
        return data

    def refresh_access_token(self):
        """Refresh expired access token"""
        url = "https://services.leadconnectorhq.com/oauth/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
        }
        r = requests.post(url, data=payload)
        r.raise_for_status()
        data = r.json()
        self._store_tokens(data)
        return data

    def _store_tokens(self, data):
        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token", self.refresh_token)
        self.token_expiry = time.time() + data.get("expires_in", 3600)

    def _ensure_token(self):
        if not self.access_token:
            raise Exception("Access token not set. Use get_access_token(code) first.")
        if self.token_expiry and time.time() > self.token_expiry - 30:
            self.refresh_access_token()

    def request(self, method, endpoint, params=None, data=None, json=None):
        """Generic request wrapper"""
        self._ensure_token()
        url = f"{self.BASE_URL}{endpoint}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        r = requests.request(method, url, headers=headers, params=params, data=data, json=json)
        r.raise_for_status()
        return r.json()

    # Convenience methods
    def get(self, endpoint, params=None):
        return self.request("GET", endpoint, params=params)

    def post(self, endpoint, data=None, json=None):
        return self.request("POST", endpoint, data=data, json=json)

    def put(self, endpoint, data=None, json=None):
        return self.request("PUT", endpoint, data=data, json=json)

    def delete(self, endpoint, params=None):
        return self.request("DELETE", endpoint, params=params)
