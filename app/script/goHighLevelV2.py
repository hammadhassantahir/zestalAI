import requests
from datetime import datetime

class GoHighLevelAPI:
    API_URL = "https://services.leadconnectorhq.com"
    
    def __init__(self, access_token, location_id):
        """Initialize with Private Integration Token and Location ID."""
        self.access_token = access_token
        self.location_id = location_id

    def _get_headers(self):
        """Get headers for API requests."""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Version': '2021-07-28'
        }

    def get_location_info(self):
        """Get current location information."""
        url = f"{self.API_URL}/locations/{self.location_id}"
        
        response = requests.get(
            url,
            headers=self._get_headers()
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get location info: {response.text}")

    def get_contacts(self, limit=20, query=None, start_after_id=None, start_after=None):
        """Get contacts from GoHighLevel."""
        url = f"{self.API_URL}/contacts/"
        
        params = {
            "locationId": self.location_id,
            "limit": min(limit, 100)  # API allows max 100 records
        }
        
        if query:
            params["query"] = query
        if start_after_id:
            params["startAfterId"] = start_after_id
        if start_after:
            params["startAfter"] = start_after
        
        response = requests.get(
            url, 
            headers=self._get_headers(),
            params=params
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get contacts: {response.text}")

    def get_appointments(self, limit=100, page=1):
        """Get appointments from GoHighLevel."""
        url = f"{self.API_URL}/appointments/v2"
        params = {
            "locationId": self.location_id,
            "limit": limit,
            "page": page
        }
        
        response = requests.get(
            url, 
            headers=self._get_headers(),
            params=params
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get appointments: {response.text}")

    def get_conversations(self, limit=100, page=1):
        """Get conversations from GoHighLevel."""
        url = f"{self.API_URL}/conversations/v2"
        params = {
            "locationId": self.location_id,
            "limit": limit,
            "page": page
        }
        
        response = requests.get(
            url, 
            headers=self._get_headers(),
            params=params
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get conversations: {response.text}")

    def create_contact(self, contact_data):
        """Create a new contact."""
        url = f"{self.API_URL}/contacts/"
        
        # Ensure locationId is in the contact data
        if 'locationId' not in contact_data:
            contact_data['locationId'] = self.location_id
        
        response = requests.post(
            url,
            headers=self._get_headers(),
            json=contact_data
        )
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Failed to create contact: {response.text}")

    def search_contacts(self, query, limit=20):
        """Search contacts with a specific query."""
        return self.get_contacts(limit=limit, query=query)