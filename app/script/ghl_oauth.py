"""
GoHighLevel Marketplace OAuth 2.0 Client
Handles authorization, token exchange, and token refresh for marketplace apps.
"""

import requests
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class GHLOAuthClient:
    """GoHighLevel Marketplace OAuth 2.0 Client"""
    
    API_URL = "https://services.leadconnectorhq.com"
    AUTH_URL = "https://marketplace.gohighlevel.com/oauth/chooselocation"
    
    # GHL Public Key for webhook signature verification
    GHL_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAokvo/r9tVgcfZ5DysOSC
Frm602qYV0MaAiNnX9O8KxMbiyRKWeL9JpCpVpt4XHIcBOK4u3cLSqJGOLaPuXw6
dO0t6Q/ZVdAV5Phz+ZtzPL16iCGeK9po6D6JHBpbi989mmzMryUnQJezlYJ3DVfB
csedpinheNnyYeFXolrJvcsjDtfAeRx5ByHQmTnSdFUzuAnC9/GepgLT9SM4nCpv
uxmZMxrJt5Rw+VUaQ9B8JSvbMPpez4peKaJPZHBbU3OdeCVx5klVXXZQGNHOs8gF
3kvoV5rTnXV0IknLBXlcKKAQLZcY/Q9rG6Ifi9c+5vqlvHPCUJFT5XUGG5RKgOKU
J062fRtN+rLYZUV+BjafxQauvC8wSWeYja63VSUruvmNj8xkx2zE/Juc+yjLjTXp
IocmaiFeAO6fUtNjDeFVkhf5LNb59vECyrHD2SQIrhgXpO4Q3dVNA5rw576PwTzN
h/AMfHKIjE4xQA1SZuYJmNnmVZLIZBlQAF9Ntd03rfadZ+yDiOXCCs9FkHibELhC
HULgCsnuDJHcrGNd5/Ddm5hxGQ0ASitgHeMZ0kcIOwKDOzOU53lDza6/Y09T7sYJ
PQe7z0cvj7aE4B+Ax1ZoZGPzpJlZtGXCsu9aTEGEnKzmsFqwcSsnw3JB31IGKAyk
T1hhTiaCeIY/OwwwNUY2yvcCAwEAAQ==
-----END PUBLIC KEY-----"""
    
    # Default scopes for marketplace app (valid scopes only)
    DEFAULT_SCOPES = [
        # SaaS scopes (for agency-level operations)
        "saas/location.write",  # Required to create sub-accounts
        "saas/location.readonly",
        "saas/company.readonly",
        # Location scopes
        "locations.readonly",
        "locations/tasks.readonly",
        "locations/tasks.write",
        "locations/tags.readonly",
        "locations/tags.write",
        "contacts.readonly",
        "contacts.write",
        "conversations.readonly",
        "conversations.write",
        "conversations/message.readonly",
        "conversations/message.write",
        "calendars.readonly",
        "calendars.write",
        "calendars/events.readonly",
        "calendars/events.write",
        "opportunities.readonly",
        "opportunities.write",
        "campaigns.readonly",
        "workflows.readonly",
        "users.readonly",
    ]
    
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """
        Initialize OAuth client.
        
        Args:
            client_id: Your GHL app's Client ID
            client_secret: Your GHL app's Client Secret
            redirect_uri: Your callback URL (e.g., https://app.zestal.pro/api/crm/callback)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        # Version ID is the client ID without the suffix (e.g., "69825c9724e8151cfd71c2c3")
        self.version_id = client_id.split('-')[0] if client_id and '-' in client_id else client_id
    
    def get_authorization_url(self, scopes: Optional[list] = None, state: Optional[str] = None) -> str:
        """
        Generate the OAuth authorization URL.
        
        Users visit this URL to authorize your app and select a location.
        
        Args:
            scopes: List of permission scopes (uses DEFAULT_SCOPES if not provided)
            state: Optional state parameter for CSRF protection
            
        Returns:
            Authorization URL string
        """
        scopes = scopes or self.DEFAULT_SCOPES
        scope_str = "+".join(scopes)  # GHL uses + instead of space for scopes
        
        url = (
            f"{self.AUTH_URL}"
            f"?response_type=code"
            f"&client_id={self.client_id}"
            f"&redirect_uri={self.redirect_uri}"
            f"&scope={scope_str}"
            f"&version_id={self.version_id}"
        )
        
        if state:
            url += f"&state={state}"
        
        return url
    
    def exchange_code_for_token(self, code: str, user_type: str = "Location") -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.
        
        Called after user authorizes and is redirected to your callback URL.
        
        Args:
            code: Authorization code from callback query parameter
            user_type: "Location" for sub-account or "Company" for agency
            
        Returns:
            Token data including:
            - access_token: Use for API calls (expires in ~24 hours)
            - refresh_token: Use to get new access token (expires in 1 year)
            - expires_in: Seconds until access_token expires
            - locationId: The authorized location ID
            - userId: The user who authorized
            - companyId: The company/agency ID
        """
        url = f"{self.API_URL}/oauth/token"
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "user_type": user_type,
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        response = requests.post(url, data=data, headers=headers, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.status_code} - {response.text}")
            raise Exception(f"Token exchange failed: {response.text}")
        
        token_data = response.json()
        logger.info(f"Token obtained for location: {token_data.get('locationId')}")
        
        return token_data
    
    def refresh_access_token(self, refresh_token: str, user_type: str = "Location") -> Dict[str, Any]:
        """
        Refresh an expired access token.
        
        Access tokens expire after ~24 hours. Call this before expiry.
        
        IMPORTANT: Each refresh_token can only be used ONCE!
        After refreshing, store the NEW refresh_token from the response.
        
        Args:
            refresh_token: The refresh token from previous token response
            user_type: "Location" or "Company"
            
        Returns:
            New token data (same format as exchange_code_for_token)
        """
        url = f"{self.API_URL}/oauth/token"
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "user_type": user_type,
        }
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        response = requests.post(url, data=data, headers=headers, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
            raise Exception(f"Token refresh failed: {response.text}")
        
        token_data = response.json()
        logger.info(f"Token refreshed for location: {token_data.get('locationId')}")
        
        return token_data
    
    def get_location_token_from_company(
        self, company_access_token: str, company_id: str, location_id: str
    ) -> Dict[str, Any]:
        """
        Generate a location access token from a company/agency token.
        
        Use this when you have an agency-level token and need to access
        a specific sub-account/location.
        
        Args:
            company_access_token: Agency-level access token
            company_id: The company/agency ID
            location_id: The target location ID
            
        Returns:
            Location-specific token data
        """
        url = f"{self.API_URL}/oauth/locationToken"
        
        data = {
            "companyId": company_id,
            "locationId": location_id,
        }
        
        headers = {
            "Authorization": f"Bearer {company_access_token}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Version": "2021-07-28",
        }
        
        response = requests.post(url, data=data, headers=headers, timeout=30)
        
        # GHL returns 201 for this endpoint
        if response.status_code not in (200, 201):
            logger.error(f"Location token failed: {response.status_code} - {response.text}")
            raise Exception(f"Failed to get location token: {response.text}")
        
        return response.json()
    
    @staticmethod
    def verify_webhook_signature(payload: str, signature: str) -> bool:
        """
        Verify webhook request authenticity.
        
        GHL signs webhook payloads with their private key.
        Verify using their public key to ensure the request is genuine.
        
        Args:
            payload: Raw JSON payload string from webhook request body
            signature: Value of 'x-wh-signature' header
            
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.primitives.serialization import load_pem_public_key
            
            public_key = load_pem_public_key(GHLOAuthClient.GHL_PUBLIC_KEY.encode())
            
            signature_bytes = base64.b64decode(signature)
            
            public_key.verify(
                signature_bytes,
                payload.encode(),
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            
            return True
        except Exception as e:
            logger.warning(f"Webhook signature verification failed: {e}")
            return False
    
    @staticmethod
    def calculate_token_expiry(expires_in: int) -> datetime:
        """
        Calculate the absolute expiry datetime from expires_in seconds.
        
        Args:
            expires_in: Number of seconds until token expires
            
        Returns:
            datetime when the token will expire
        """
        return datetime.utcnow() + timedelta(seconds=expires_in)
