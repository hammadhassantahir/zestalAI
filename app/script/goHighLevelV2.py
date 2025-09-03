import requests
from datetime import datetime, timedelta

class GoHighLevelAPI:
    BASE_URL = "https://marketplace.gohighlevel.com"
    # BASE_URL = "https://services.leadconnectorhq.com"
    
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None

    def get_auth_url(self):
        """Generate the authorization URL for GoHighLevel OAuth."""
        scopes = [
            # "contacts.readonly",
            # "contacts.write",
            # "conversations.readonly",
            # "conversations.write",
            # "appointments.readonly",
            # "appointments.write",
            "locations.readonly"  # Required for location access
        ]
        
        return (
            f"https://marketplace.gohighlevel.com/oauth/chooselocation"
            f"?client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&response_type=code"
            f"&scope={' '.join(scopes)}"  # Space-separated instead of comma-separated
        )

    def exchange_code_for_token(self, auth_code):
        """Exchange authorization code for access token."""
        url = f"{self.BASE_URL}/oauth/token"
        
        # Create multipart form data
        files = {
            'client_id': (None, self.client_id),
            'client_secret': (None, self.client_secret),
            'grant_type': (None, 'authorization_code'),
            'code': (None, auth_code),
            'redirect_uri': (None, self.redirect_uri)
        }
        
        headers = {
            'Accept': 'application/json'
        }
        
        print(f"Sending token request to {url}")  # Debug logging
        print(f"With files: {files}")  # Debug logging
        
        # Use requests with multipart form data
        response = requests.post(
            url, 
            files=files,  # Use files for multipart/form-data
            headers=headers
        )
        
        print(f"Token exchange response: {response.status_code} - {response.text}")  # Debug logging
        
        if response.status_code == 200:
            data = response.json()
            self._update_tokens(data)
            return data
        else:
            raise Exception(f"Failed to get token: {response.text}")

    def refresh_access_token(self):
        """Refresh the access token using the refresh token."""
        if not self.refresh_token:
            raise Exception("No refresh token available")
            
        url = f"{self.BASE_URL}/oauth/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            self._update_tokens(data)
            return data
        else:
            raise Exception(f"Failed to refresh token: {response.text}")

    def _update_tokens(self, token_data):
        """Update token information."""
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data.get("refresh_token", self.refresh_token)
        expires_in = token_data.get("expires_in", 86400)  # Default 24 hours
        self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

    def _get_headers(self):
        """Get headers for API requests with token refresh if needed."""
        if self.token_expires_at and datetime.now() >= self.token_expires_at:
            self.refresh_access_token()
            
        if not self.access_token:
            raise Exception("No access token available")
            
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Version": "2021-07-28",
            "Content-Type": "application/json"
        }

    # API Methods
    def get_contacts(self, limit=100, page=1):
        """Get contacts from GoHighLevel."""
        url = f"{self.BASE_URL}/contacts/"
        params = {"limit": limit, "page": page}
        response = requests.get(url, headers=self._get_headers(), params=params)
        return response.json()

    def get_appointments(self, limit=100, page=1):
        """Get appointments from GoHighLevel."""
        url = f"{self.BASE_URL}/appointments/v2"
        params = {"limit": limit, "page": page}
        response = requests.get(url, headers=self._get_headers(), params=params)
        return response.json()

    def get_conversations(self, limit=100, page=1):
        """Get conversations from GoHighLevel."""
        url = f"{self.BASE_URL}/conversations/v2"
        params = {"limit": limit, "page": page}
        response = requests.get(url, headers=self._get_headers(), params=params)
        return response.json()
