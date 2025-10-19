#!/usr/bin/env python3
"""
Facebook Background Service
Periodically fetches user posts and comments from Facebook API
Run this script as a cron job or background service
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, project_root)

from app import create_app
from flask import current_app
from app.models import User
from app.services.facebook_service import FacebookService
from app.extensions import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/facebook_service.log'),
        logging.StreamHandler()
    ]
)

def fetch_all_user_posts():
    """Fetch posts for all users with valid Facebook tokens"""
    try:
        app = create_app()
        
        with app.app_context():
            # Get all users with Facebook access tokens that haven't expired
            users = User.query.filter(
                User.facebook_access_token.isnot(None),
                User.facebook_token_expires > datetime.utcnow()
            ).all()
            
            logging.info(f"Found {len(users)} users with valid Facebook tokens")
            
            for user in users:
                try:
                    logging.info(f"Fetching posts for user {user.id} ({user.email})")
                    
                    # Fetch posts with a reasonable limit
                    limit = current_app.config['FACEBOOK_POST_LIMIT']
                    result = FacebookService.fetch_user_posts(user.id, limit=limit)
                    
                    if 'error' in result:
                        logging.error(f"Error fetching posts for user {user.id}: {result['error']}")
                        continue
                    
                    posts_count = result.get('posts_count', 0)
                    logging.info(f"Successfully fetched {posts_count} posts for user {user.id}")
                    
                    # Small delay between users to be respectful to Facebook API
                    time.sleep(1)
                    
                except Exception as e:
                    logging.error(f"Error processing user {user.id}: {str(e)}")
                    continue
            
            logging.info("Completed fetching posts for all users")
            
    except Exception as e:
        logging.error(f"Error in fetch_all_user_posts: {str(e)}")

def cleanup_expired_tokens():
    """Clean up expired Facebook tokens"""
    try:
        app = create_app()
        
        with app.app_context():
            expired_users = User.query.filter(
                User.facebook_access_token.isnot(None),
                User.facebook_token_expires < datetime.utcnow()
            ).all()
            
            logging.info(f"Found {len(expired_users)} users with expired tokens")
            
            for user in expired_users:
                logging.info(f"Clearing expired token for user {user.id} ({user.email})")
                user.facebook_access_token = None
                user.facebook_token_expires = None
                db.session.commit()
            
            logging.info("Completed token cleanup")
            
    except Exception as e:
        logging.error(f"Error in cleanup_expired_tokens: {str(e)}")

def main():
    """Main function to run the background service manually"""
    logging.info("Starting Facebook background service (manual execution)")
    
    # Fetch posts for all users
    fetch_all_user_posts()
    
    # Clean up expired tokens
    cleanup_expired_tokens()
    
    logging.info("Facebook background service completed")

if __name__ == "__main__":
    main()
