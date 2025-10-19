import requests
from flask import current_app
import logging
from datetime import datetime, timedelta
from ..models import User, FacebookPost, FacebookComment
from ..extensions import db
from urllib.parse import urlparse, parse_qs

class FacebookService:
    """Service for fetching and managing Facebook posts and comments"""
    
    @staticmethod
    def fetch_user_posts(user_id, limit=50):
        """Fetch recent posts for a user from Facebook API"""
        try:
            user = User.query.get(user_id)
            if not user or not user.facebook_access_token:
                logging.error(f"User {user_id} not found or no Facebook access token")
                return {'error': 'User not found or no Facebook access token'}
            
            # Check if token is expired or expiring soon
            if user.facebook_token_expires and user.facebook_token_expires < datetime.utcnow():
                logging.error(f"Facebook access token expired for user {user_id}")
                return {'error': 'Facebook access token expired'}
            
            # Check if token expires within 7 days and try to refresh
            if user.facebook_token_expires:
                days_until_expiry = (user.facebook_token_expires - datetime.utcnow()).days
                if days_until_expiry <= 7:
                    logging.info(f"Token expires in {days_until_expiry} days, attempting refresh...")
                    refresh_result = FacebookService.refresh_facebook_token(user_id)
                    if 'error' in refresh_result:
                        logging.warning(f"Token refresh failed: {refresh_result['error']}")
                        # Continue with existing token if refresh fails
                    else:
                        logging.info("Token refreshed successfully")
                        # Reload user to get updated token
                        user = User.query.get(user_id)
            
            # Fetch posts from Facebook API
            fields = '{id,message,story,type,permalink_url,created_time,updated_time}'
            # url = f"https://graph.facebook.com/me/posts?fields={fields}&limit={limit}&access_token={user.facebook_access_token}"
            url = f"https://graph.facebook.com/me?fields=posts.limit({limit}){fields}&access_token={user.facebook_access_token}"
            print(url)
            
            response = requests.get(url, timeout=100)
            if user_id == 4:
                print(f"*************** Response: {response.text}")
            # print(f"*************** Response: {response.text}")
            print(f"*************** Response status code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                if user_id == 4:
                    print(f"*************** Data: {data}")
                posts_data = data.get('posts', {}).get('data', [])
                
                saved_posts = []
                print(f"*************** Posts data Count: {len(posts_data)}")
                for post_data in posts_data:
                    saved_post = FacebookService._save_post(user_id, post_data)
                    if saved_post:
                        saved_posts.append(saved_post)
                        # TODO: Fetch comments for this post (commented out to avoid API issues)
                        # FacebookService.fetch_post_comments(saved_post.id, user.facebook_access_token)
                
                # Get pagination info
                paging = data.get('posts', {}).get('paging', {})
                next_url = paging.get('next')
                next_paging_token = None
                try:
                    # Parse the URL
                    parsed = urlparse(next_url)
                    # Get query parameters as dict
                    params = parse_qs(parsed.query)
                    # Extract the paging token
                    next_paging_token = params.get('__paging_token', [None])[0]
                except Exception as e:
                    logging.error(f"Error parsing next URL: {str(e)}")

                
                print(f"Next paging token: {next_paging_token}")
                return {
                    'success': True,
                    'posts_count': len(saved_posts),
                    'posts': [post.to_dict() for post in saved_posts],
                    'next_url': next_url
                }
            else:
                logging.error(f"Facebook API error: {response.status_code} - {response.text}")
                return {'error': f'Facebook API error: {response.status_code}'}
                
        except Exception as e:
            logging.error(f"Error fetching user posts: {str(e)}")
            return {'error': 'Internal server error'}
    
    @staticmethod
    def _fetch_posts_from_url(url):
        """Fetch posts from a specific URL (for pagination)"""
        try:
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                posts_data = data.get('data', [])
                
                # Extract user_id from the first post or URL
                # This is a bit tricky with pagination URLs
                # We'll need to handle this carefully
                
                saved_posts = []
                for post_data in posts_data:
                    # Extract user_id from post_id (format: user_id_post_id)
                    post_id = post_data.get('id', '')
                    if '_' in post_id:
                        user_facebook_id = post_id.split('_')[0]
                        # Find user by facebook_id
                        user = User.query.filter_by(facebook_id=user_facebook_id).first()
                        if user:
                            saved_post = FacebookService._save_post(user.id, post_data)
                            if saved_post:
                                saved_posts.append(saved_post)
                
                # Get pagination info
                paging = data.get('paging', {})
                next_url = paging.get('next')
                
                return {
                    'success': True,
                    'posts_count': len(saved_posts),
                    'posts': [post.to_dict() for post in saved_posts],
                    'next_url': next_url
                }
            else:
                logging.error(f"Facebook API error: {response.status_code} - {response.text}")
                return {'error': f'Facebook API error: {response.status_code}'}
                
        except Exception as e:
            logging.error(f"Error fetching posts from URL: {str(e)}")
            return {'error': 'Internal server error'}
    
    @staticmethod
    def _save_post(user_id, post_data):
        """Save a single post to database"""
        try:
            facebook_post_id = post_data.get('id')
            
            # Check if post already exists
            existing_post = FacebookPost.query.filter_by(facebook_post_id=facebook_post_id).first()
            
            if existing_post:
                # Update existing post
                existing_post.message = post_data.get('message')
                existing_post.story = post_data.get('story')
                existing_post.post_type = post_data.get('type')
                existing_post.permalink_url = post_data.get('permalink_url')
                existing_post.updated_time = FacebookService._parse_facebook_date(post_data.get('updated_time'))
                # Handle engagement data safely
                likes_data = post_data.get('likes', {})
                comments_data = post_data.get('comments', {})
                shares_data = post_data.get('shares', {})
                
                existing_post.likes_count = likes_data.get('summary', {}).get('total_count', 0) if likes_data else 0
                existing_post.comments_count = comments_data.get('summary', {}).get('total_count', 0) if comments_data else 0
                existing_post.shares_count = shares_data.get('count', 0) if shares_data else 0
                existing_post.last_updated = datetime.utcnow()
                
                db.session.commit()
                return existing_post
            else:
                # Create new post
                new_post = FacebookPost(
                    user_id=user_id,
                    facebook_post_id=facebook_post_id,
                    message=post_data.get('message'),
                    story=post_data.get('story'),
                    post_type=post_data.get('type'),
                    permalink_url=post_data.get('permalink_url'),
                    created_time=FacebookService._parse_facebook_date(post_data.get('created_time')),
                    updated_time=FacebookService._parse_facebook_date(post_data.get('updated_time')),
                    likes_count=0,  # Will be fetched separately if needed
                    comments_count=0,  # Will be fetched separately if needed
                    shares_count=0  # Will be fetched separately if needed
                )
                
                db.session.add(new_post)
                db.session.commit()
                return new_post
                
        except Exception as e:
            logging.error(f"Error saving post: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def fetch_post_comments(post_id, access_token, limit=25):
        """Fetch comments for a specific post"""
        try:
            post = FacebookPost.query.get(post_id)
            if not post:
                return {'error': 'Post not found'}
            
            # Fetch comments from Facebook API
            fields = 'id,message,from,created_time,like_count'
            url = f"https://graph.facebook.com/{post.facebook_post_id}/comments?fields={fields}&limit={limit}&access_token={access_token}"
            
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                comments_data = data.get('data', [])
                
                saved_comments = []
                for comment_data in comments_data:
                    saved_comment = FacebookService._save_comment(post_id, comment_data)
                    if saved_comment:
                        saved_comments.append(saved_comment)
                
                return {
                    'success': True,
                    'comments_count': len(saved_comments),
                    'comments': [comment.to_dict() for comment in saved_comments]
                }
            else:
                logging.error(f"Facebook API error for comments: {response.status_code} - {response.text}")
                return {'error': f'Facebook API error: {response.status_code}'}
                
        except Exception as e:
            logging.error(f"Error fetching post comments: {str(e)}")
            return {'error': 'Internal server error'}
    
    @staticmethod
    def _save_comment(post_id, comment_data):
        """Save a single comment to database"""
        try:
            facebook_comment_id = comment_data.get('id')
            
            # Check if comment already exists
            existing_comment = FacebookComment.query.filter_by(facebook_comment_id=facebook_comment_id).first()
            
            if existing_comment:
                # Update existing comment
                existing_comment.message = comment_data.get('message')
                existing_comment.likes_count = comment_data.get('like_count', 0)
                db.session.commit()
                return existing_comment
            else:
                # Create new comment
                from_data = comment_data.get('from', {})
                new_comment = FacebookComment(
                    post_id=post_id,
                    facebook_comment_id=facebook_comment_id,
                    message=comment_data.get('message'),
                    from_id=from_data.get('id'),
                    from_name=from_data.get('name'),
                    created_time=FacebookService._parse_facebook_date(comment_data.get('created_time')),
                    likes_count=comment_data.get('like_count', 0)
                )
                
                db.session.add(new_comment)
                db.session.commit()
                return new_comment
                
        except Exception as e:
            logging.error(f"Error saving comment: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def _parse_facebook_date(date_string):
        """Parse Facebook date string to datetime object"""
        if not date_string:
            return None
        try:
            # Facebook dates are in ISO format with timezone
            # Example: "2023-12-01T10:30:00+0000"
            if '+' in date_string:
                date_string = date_string.split('+')[0]
            return datetime.fromisoformat(date_string.replace('T', ' '))
        except Exception as e:
            logging.error(f"Error parsing Facebook date '{date_string}': {str(e)}")
            return None
    
    @staticmethod
    def get_user_posts_from_db(user_id, limit=20, offset=0):
        """Get user's Facebook posts from database"""
        try:
            posts = FacebookPost.query.filter_by(user_id=user_id)\
                                    .order_by(FacebookPost.created_time.desc())\
                                    .limit(limit)\
                                    .offset(offset)\
                                    .all()
            
            posts_with_comments = []
            for post in posts:
                post_dict = post.to_dict()
                post_dict['comments'] = [comment.to_dict() for comment in post.comments]
                posts_with_comments.append(post_dict)
            
            return {
                'success': True,
                'posts': posts_with_comments,
                'total': FacebookPost.query.filter_by(user_id=user_id).count()
            }
            
        except Exception as e:
            logging.error(f"Error getting user posts from DB: {str(e)}")
            return {'error': 'Internal server error'}
    
    @staticmethod
    def refresh_facebook_token(user_id, short_lived_token=None):
        """Refresh Facebook access token to long-lived token"""
        try:
            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}
            
            # Use provided token or user's existing token
            token_to_refresh = short_lived_token or user.facebook_access_token
            if not token_to_refresh:
                return {'error': 'No Facebook access token available'}
            
            # Get app credentials from config
            from ..config import Config
            config = Config()
            app_id = config.FACEBOOK_APP_ID
            app_secret = config.FACEBOOK_APP_SECRET
            
            if not app_id or not app_secret:
                logging.error("Facebook app credentials not configured")
                return {'error': 'Facebook app not configured'}
            
            # Exchange short-lived token for long-lived token
            url = f"https://graph.facebook.com/v18.0/oauth/access_token"
            params = {
                'grant_type': 'fb_exchange_token',
                'client_id': app_id,
                'client_secret': app_secret,
                'fb_exchange_token': token_to_refresh
            }
            
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                new_access_token = data.get('access_token')
                expires_in = data.get('expires_in')  # seconds
                
                if new_access_token:
                    # Calculate expiration time
                    new_expires_at = datetime.utcnow() + timedelta(seconds=expires_in) if expires_in else None
                    
                    # Update user's token
                    user.facebook_access_token = new_access_token
                    user.facebook_token_expires = new_expires_at
                    db.session.commit()
                    
                    logging.info(f"Successfully refreshed Facebook token for user {user_id}")
                    return {
                        'success': True,
                        'access_token': new_access_token,
                        'expires_in': expires_in,
                        'expires_at': new_expires_at.isoformat() if new_expires_at else None
                    }
                else:
                    logging.error(f"No access token in Facebook response: {data}")
                    return {'error': 'No access token received from Facebook'}
            else:
                logging.error(f"Facebook token refresh error: {response.status_code} - {response.text}")
                return {'error': f'Facebook API error: {response.status_code}'}
                
        except Exception as e:
            logging.error(f"Error refreshing Facebook token: {str(e)}")
            return {'error': 'Internal server error'}
    
    @staticmethod
    def check_and_refresh_token_if_needed(user_id):
        """Check if token is expired or expiring soon and refresh if needed"""
        try:
            user = User.query.get(user_id)
            if not user or not user.facebook_access_token:
                return {'error': 'User not found or no Facebook access token'}
            
            # Check if token expires within 7 days
            if user.facebook_token_expires:
                days_until_expiry = (user.facebook_token_expires - datetime.utcnow()).days
                if days_until_expiry <= 7:
                    logging.info(f"Token expires in {days_until_expiry} days, refreshing...")
                    return FacebookService.refresh_facebook_token(user_id)
            
            return {'success': True, 'message': 'Token is still valid'}
            
        except Exception as e:
            logging.error(f"Error checking token expiry: {str(e)}")
            return {'error': 'Internal server error'}