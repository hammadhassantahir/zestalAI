"""
GoHighLevel OAuth Token Model
Stores OAuth tokens for marketplace app installations.
"""

from datetime import datetime
from app.extensions import db


class GHLToken(db.Model):
    """
    Store OAuth tokens for GHL marketplace app installations.
    
    Each row represents one location's access to your marketplace app.
    The agency token (is_agency=True) is used to create sub-accounts and generate location tokens.
    """
    __tablename__ = 'ghl_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Location/Company identification
    location_id = db.Column(db.String(50), unique=True, nullable=True, index=True)
    company_id = db.Column(db.String(50), nullable=True, index=True)
    user_id = db.Column(db.String(50), nullable=True)  # GHL user who authorized
    
    # Optional: Link to your app's user
    app_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # OAuth tokens
    access_token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text, nullable=False)
    token_type = db.Column(db.String(20), default='Bearer')
    
    # Token metadata
    expires_at = db.Column(db.DateTime, nullable=False)  # When access_token expires
    scope = db.Column(db.Text, nullable=True)  # Granted scopes
    user_type = db.Column(db.String(20), default='Location')  # 'Location' or 'Company'
    is_agency = db.Column(db.Boolean, default=False)  # True for agency-level token
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def is_expired(self) -> bool:
        """Check if the access token has expired."""
        return datetime.utcnow() >= self.expires_at
    
    def expires_soon(self, minutes: int = 30) -> bool:
        """Check if the token expires within the specified minutes."""
        from datetime import timedelta
        return datetime.utcnow() >= (self.expires_at - timedelta(minutes=minutes))
    
    def update_tokens(self, token_data: dict):
        """Update tokens from a refresh response."""
        from app.script.ghl_oauth import GHLOAuthClient
        
        self.access_token = token_data['access_token']
        self.refresh_token = token_data['refresh_token']
        self.expires_at = GHLOAuthClient.calculate_token_expiry(token_data['expires_in'])
        if 'scope' in token_data:
            self.scope = token_data['scope']
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Return token info (without sensitive data)."""
        return {
            'id': self.id,
            'location_id': self.location_id,
            'company_id': self.company_id,
            'user_type': self.user_type,
            'is_expired': self.is_expired(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def get_by_location(cls, location_id: str) -> 'GHLToken':
        """Get token by location ID."""
        return cls.query.filter_by(location_id=location_id).first()
    
    @classmethod
    def create_or_update(cls, token_data: dict) -> 'GHLToken':
        """Create or update a token record from OAuth response."""
        from app.script.ghl_oauth import GHLOAuthClient
        
        location_id = token_data.get('locationId')
        
        token = cls.query.filter_by(location_id=location_id).first()
        
        if token:
            token.update_tokens(token_data)
        else:
            token = cls(
                location_id=location_id,
                company_id=token_data.get('companyId'),
                user_id=token_data.get('userId'),
                access_token=token_data['access_token'],
                refresh_token=token_data['refresh_token'],
                expires_at=GHLOAuthClient.calculate_token_expiry(token_data['expires_in']),
                scope=token_data.get('scope'),
                user_type=token_data.get('userType', 'Location'),
            )
            db.session.add(token)
        
        db.session.commit()
        return token
    
    @classmethod
    def get_agency_token(cls) -> 'GHLToken':
        """Get the agency-level token (there should only be one)."""
        return cls.query.filter_by(is_agency=True).first()
    
    @classmethod
    def create_or_update_agency(cls, token_data: dict) -> 'GHLToken':
        """Create or update the agency-level token from OAuth response."""
        from app.script.ghl_oauth import GHLOAuthClient
        
        # There should only be one agency token
        token = cls.query.filter_by(is_agency=True).first()
        
        if token:
            token.update_tokens(token_data)
            token.company_id = token_data.get('companyId')
        else:
            token = cls(
                location_id=None,  # Agency tokens don't have a location
                company_id=token_data.get('companyId'),
                user_id=token_data.get('userId'),
                access_token=token_data['access_token'],
                refresh_token=token_data['refresh_token'],
                expires_at=GHLOAuthClient.calculate_token_expiry(token_data['expires_in']),
                scope=token_data.get('scope'),
                user_type='Company',
                is_agency=True,
            )
            db.session.add(token)
        
        db.session.commit()
        return token
    
    @classmethod
    def create_location_token(cls, location_id: str, token_data: dict, app_user_id: int = None) -> 'GHLToken':
        """Create a location token from agency-generated token data."""
        from app.script.ghl_oauth import GHLOAuthClient
        
        token = cls(
            location_id=location_id,
            company_id=token_data.get('companyId'),
            user_id=token_data.get('userId'),
            app_user_id=app_user_id,
            access_token=token_data['access_token'],
            refresh_token=token_data.get('refresh_token', ''),  # May not have refresh
            expires_at=GHLOAuthClient.calculate_token_expiry(token_data.get('expires_in', 86400)),
            scope=token_data.get('scope'),
            user_type='Location',
            is_agency=False,
        )
        db.session.add(token)
        db.session.commit()
        return token
    
    def __repr__(self):
        return f'<GHLToken location={self.location_id} is_agency={self.is_agency}>'
