#!/usr/bin/env python3
"""
Generate OAuth tokens for existing users who have GHL location IDs but missing tokens.

Usage:
    python generate_user_tokens.py [--user-id USER_ID] [--force]

Options:
    --user-id   Generate token for specific user only
    --force     Regenerate tokens even if they exist
"""

import argparse
import os
import sys

# Add project root directory to path (go up 2 levels from this script)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from app import create_app
from app.models.ghl_token import GHLToken
from app.models.user import User
from app.script.ghl_oauth import GHLOAuthClient


def generate_tokens(user_id=None, force=False):
    """Generate OAuth tokens for users with GHL locations."""
    
    app = create_app()
    with app.app_context():
        # Get agency token
        agency_token = GHLToken.get_agency_token()
        if not agency_token:
            print('❌ No agency token found! Please authorize the marketplace app first.')
            print('   Visit: /api/crm/install')
            return False
        
        print(f'Using agency token for company: {agency_token.company_id}')
        
        # Initialize OAuth client
        oauth_client = GHLOAuthClient(
            client_id=os.environ.get('GHL_CLIENT_ID'),
            client_secret=os.environ.get('GHL_CLIENT_SECRET'),
            redirect_uri=os.environ.get('GHL_REDIRECT_URI')
        )
        
        # Get users
        if user_id:
            users = User.query.filter_by(id=user_id).all()
            if not users:
                print(f'❌ User with ID {user_id} not found')
                return False
        else:
            users = User.query.filter(User.ghl_location_id.isnot(None)).all()
        
        print(f'\nFound {len(users)} users with GHL location IDs\n')
        
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for user in users:
            if not user.ghl_location_id:
                print(f'  ⚠️  User {user.id} ({user.email}): No location ID')
                skip_count += 1
                continue
            
            # Check if token already exists
            existing = GHLToken.get_by_location(user.ghl_location_id)
            if existing and not force:
                print(f'  ✓ User {user.id} ({user.email}): Token exists (use --force to regenerate)')
                skip_count += 1
                continue
            
            # Delete existing token if force mode
            if existing and force:
                from app.extensions import db
                db.session.delete(existing)
                db.session.commit()
                print(f'  🔄 User {user.id}: Deleted existing token')
            
            # Generate new token
            try:
                location_token_data = oauth_client.get_location_token_from_company(
                    company_access_token=agency_token.access_token,
                    company_id=agency_token.company_id,
                    location_id=user.ghl_location_id
                )
                
                token = GHLToken.create_location_token(
                    location_id=user.ghl_location_id,
                    token_data=location_token_data,
                    app_user_id=user.id
                )
                print(f'  ✅ User {user.id} ({user.email}): Token created (ID: {token.id})')
                success_count += 1
                
            except Exception as e:
                print(f'  ❌ User {user.id} ({user.email}): Failed - {e}')
                error_count += 1
        
        print(f'\n{"="*50}')
        print(f'Summary:')
        print(f'  ✅ Created: {success_count}')
        print(f'  ✓  Skipped: {skip_count}')
        print(f'  ❌ Errors:  {error_count}')
        print(f'{"="*50}')
        
        return error_count == 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate OAuth tokens for existing users')
    parser.add_argument('--user-id', type=int, help='Generate token for specific user only')
    parser.add_argument('--force', action='store_true', help='Regenerate tokens even if they exist')
    
    args = parser.parse_args()
    
    success = generate_tokens(user_id=args.user_id, force=args.force)
    sys.exit(0 if success else 1)
