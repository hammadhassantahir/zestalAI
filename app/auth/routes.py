from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from ..extensions import db
from ..models.user import User
from ..services.email_service import send_verification_email, send_reset_password_email
from ..services.facebook_service import FacebookService
import secrets
import requests
import logging

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        logging.info("Login attempt received")
        data = request.get_json()
        logging.info(f"Login request data: {data}")
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        logging.info(f"User found: {user is not None}")
        
        if not user:
            return jsonify({'error': 'Invalid email or password', 'details': 'User not found'}), 401
        
        if not user.check_password(data['password']):
            return jsonify({'error': 'Invalid email or password', 'details': 'Wrong password'}), 401
        
        if not user.is_verified:
            return jsonify({'error': 'Please verify your email first'}), 403
        
        access_token = create_access_token(identity=str(user.id))
        
        response_data = {
            'access_token': access_token,
            'user': user.to_dict(),
            'message': 'Login successful'
        }
        logging.info("Login successful")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logging.error(f"Error in login: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/signup', methods=['POST', 'OPTIONS'])
def signup():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        data = request.get_json()
        logging.info(f"Signup request data: {data}")
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email', 'password']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create new user
        user = User(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            is_verified=True,
            code=secrets.token_urlsafe(32)
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'user': user.to_dict()
        }), 201
    except Exception as e:
        logging.error(f"Error in signup: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/facebook/login', methods=['POST', 'OPTIONS'])
def facebook_login():
    """Handle Facebook login with access token"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
        
    try:
        data = request.get_json()
        logging.info(f"Facebook login request received with data: {data}")
        
        if not data:
            logging.error("No JSON data received in Facebook login request")
            return jsonify({'error': 'No data provided'}), 400
            
        if not data.get('access_token'):
            logging.error("No access token provided in Facebook login request")
            return jsonify({'error': 'Facebook access token is required'}), 400
        
        access_token = data['access_token']
        logging.info("Facebook login attempt received with token")
        
        # Verify the Facebook access token and get user info
        fb_user_info, token_expires = verify_facebook_token(access_token)
        if not fb_user_info:
            return jsonify({'error': 'Invalid Facebook access token'}), 401
        
        facebook_id = fb_user_info['id']
        email = fb_user_info.get('email')
        first_name = fb_user_info.get('first_name', '')
        last_name = fb_user_info.get('last_name', '')
        
        if not email:
            return jsonify({'error': 'Email is required from Facebook'}), 400
        
        # Check if user exists by Facebook ID or email
        user = User.query.filter_by(facebook_id=facebook_id).first()
        if not user:
            user = User.query.filter_by(email=email).first()
        
        if user:
            # Update Facebook ID and access token if not set
            if not user.facebook_id:
                user.facebook_id = facebook_id
            # Always update the access token and expiration
            user.facebook_access_token = access_token
            user.facebook_token_expires = token_expires
            db.session.commit()
        else:
            # Create new user
            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                facebook_id=facebook_id,
                facebook_access_token=access_token,
                facebook_token_expires=token_expires,
                is_verified=True,  # Facebook users are pre-verified
                code=secrets.token_urlsafe(32)
            )
            db.session.add(user)
            db.session.commit()
            logging.info(f"New Facebook user created: {email}")
        
        # Create JWT access token
        access_token = create_access_token(identity=str(user.id))
        
        response_data = {
            'access_token': access_token,
            'user': user.to_dict(),
            'message': 'Facebook login successful'
        }
        
        logging.info(f"Facebook login successful for user: {email}")
        return jsonify(response_data), 200
        
    except Exception as e:
        logging.error(f"Error in Facebook login: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/facebook/callback', methods=['GET'])
def facebook_callback():
    """Handle Facebook OAuth callback (matches FACEBOOK_OAUTH_REDIRECT_URI)"""
    try:
        # This route handles the callback URI configured in Facebook app settings
        code = request.args.get('code')
        state = request.args.get('state')
        
        if code:
            logging.info(f"Facebook OAuth callback received - Code: {code}, State: {state}")
            # Here you can implement the full OAuth flow if needed
            # For now, we'll return the code for frontend processing
            return jsonify({
                'message': 'OAuth callback successful',
                'code': code,
                'state': state
            })
        else:
            error = request.args.get('error')
            error_reason = request.args.get('error_reason', 'Unknown error')
            return jsonify({
                'error': 'OAuth callback failed',
                'error_code': error,
                'error_reason': error_reason
            }), 400
            
    except Exception as e:
        logging.error(f"Error in Facebook callback: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/facebook/redirect', methods=['GET'])
def facebook_redirect():
    """Handle Facebook OAuth redirect (matches FACEBOOK_OAUTH_REDIRECT_URI)"""
    try:
        # This route handles the redirect URI configured in Facebook app settings
        code = request.args.get('code')
        state = request.args.get('state')
        
        if code:
            logging.info(f"Facebook OAuth redirect received - Code: {code}, State: {state}")
            # Here you can implement the full OAuth flow if needed
            # For now, we'll redirect to the frontend with the code
            frontend_url = current_app.config.get('FRONTEND_URL', 'http://localhost:3000')
            redirect_url = f"{frontend_url}/auth/facebook/callback?code={code}"
            if state:
                redirect_url += f"&state={state}"
            
            return jsonify({
                'message': 'OAuth redirect successful',
                'redirect_url': redirect_url,
                'code': code,
                'state': state
            })
        else:
            error = request.args.get('error')
            error_reason = request.args.get('error_reason', 'Unknown error')
            return jsonify({
                'error': 'OAuth redirect failed',
                'error_code': error,
                'error_reason': error_reason
            }), 400
            
    except Exception as e:
        logging.error(f"Error in Facebook redirect: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

def verify_facebook_token(access_token):
    """Verify Facebook access token and return user info with token expiration"""
    try:
        # First verify the token's validity and get expiration
        debug_url = f"https://graph.facebook.com/debug_token?input_token={access_token}&access_token={access_token}"
        debug_response = requests.get(debug_url, timeout=10)
        debug_data = debug_response.json()
        
        logging.info(f"Token debug response: {debug_data}")
        
        if not debug_response.ok or not debug_data.get('data', {}).get('is_valid'):
            logging.error(f"Invalid Facebook token: {debug_data}")
            return None, None
            
        # Get token expiration timestamp
        expires_at = debug_data.get('data', {}).get('expires_at')
        token_expires = None
        if expires_at:
            token_expires = datetime.fromtimestamp(expires_at)
            
        # If token is valid, get user info
        url = f"https://graph.facebook.com/me?fields=id,email,first_name,last_name&access_token={access_token}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            user_data = response.json()
            logging.info(f"Facebook user data retrieved: {user_data.get('email', 'No email')}")
            
            # Verify we got all required fields
            required_fields = ['id', 'email']
            missing_fields = [field for field in required_fields if not user_data.get(field)]
            
            if missing_fields:
                logging.error(f"Missing required fields from Facebook: {missing_fields}")
                return None, None
                
            return user_data, token_expires
        else:
            logging.error(f"Facebook API error: {response.status_code} - {response.text}")
            return None, None
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Error verifying Facebook token: {str(e)}")
        return None, None
    except Exception as e:
        logging.error(f"Unexpected error verifying Facebook token: {str(e)}")
        return None, None

@auth_bp.route('/check-email', methods=['POST'])
def check_email():
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
            
        user = User.query.filter_by(email=email).first()
        if user:
            return jsonify({
                'exists': True,
                'is_verified': user.is_verified
            })
        
        return jsonify({'exists': False})
        
    except Exception as e:
        logging.error(f"Error in check_email: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/verify', methods=['GET'])
@jwt_required()
def verify_token():
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user)
        if not user:
            return jsonify({"valid": False, "error": "User not found"}), 404
        
        if not user.is_verified:
            return jsonify({"valid": False, "error": "User not verified"}), 403
        
        return jsonify({"valid": True, "user_id": current_user, "user": user.to_dict()}), 200
    except:
        return jsonify({"valid": False}), 401

@auth_bp.route('/facebook/webhook', methods=['GET', 'POST'])
def facebook_webhook():
    """Handle Facebook webhook verification and event notifications"""
    try:
        if request.method == 'GET':
            # Handle webhook verification
            return verify_facebook_webhook()
        elif request.method == 'POST':
            # Handle webhook events
            return handle_facebook_webhook_event()
    except Exception as e:
        logging.error(f"Error in Facebook webhook: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

def verify_facebook_webhook():
    """Verify Facebook webhook subscription request"""
    try:
        # Facebook sends these parameters for verification
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        logging.info(f"Facebook webhook verification - Mode: {mode}, Token present: {token is not None}")
        
        # Check if this is a verification request
        if mode and token:
            # Verify the mode and token
            if mode == 'subscribe' and token == current_app.config.get('FACEBOOK_WEBHOOK_VERIFY_TOKEN'):
                logging.info("Facebook webhook verification successful")
                # Respond with the challenge token from the request
                return challenge, 200
            else:
                logging.error(f"Facebook webhook verification failed - Invalid token or mode")
                return 'Forbidden', 403
        else:
            logging.error("Facebook webhook verification failed - Missing parameters")
            return 'Bad Request', 400
            
    except Exception as e:
        logging.error(f"Error in Facebook webhook verification: {str(e)}")
        return 'Internal Server Error', 500

def handle_facebook_webhook_event():
    """Handle incoming Facebook webhook events"""
    try:
        # Get the request body
        body = request.get_json()
        
        if not body:
            logging.error("Facebook webhook event: No JSON body received")
            return 'Bad Request', 400
        
        logging.info(f"Facebook webhook event received: {body}")
        
        # Verify the request is from Facebook (optional but recommended)
        # You can implement signature verification here if needed
        
        # Process the webhook payload
        if body.get('object') == 'page':
            # Handle page events
            for entry in body.get('entry', []):
                page_id = entry.get('id')
                time = entry.get('time')
                
                logging.info(f"Processing page event for page {page_id} at {time}")
                
                # Handle messaging events
                if 'messaging' in entry:
                    for messaging_event in entry['messaging']:
                        handle_messaging_event(messaging_event, page_id)
                
                # Handle changes (field updates)
                if 'changes' in entry:
                    for change in entry['changes']:
                        handle_field_change(change, page_id)
        
        elif body.get('object') == 'user':
            # Handle user events
            for entry in body.get('entry', []):
                user_id = entry.get('id')
                time = entry.get('time')
                
                logging.info(f"Processing user event for user {user_id} at {time}")
                
                # Handle user field changes
                if 'changes' in entry:
                    for change in entry['changes']:
                        handle_user_change(change, user_id)
        
        # Return 200 OK to acknowledge receipt
        return 'EVENT_RECEIVED', 200
        
    except Exception as e:
        logging.error(f"Error handling Facebook webhook event: {str(e)}")
        return 'Internal Server Error', 500

def handle_messaging_event(messaging_event, page_id):
    """Handle individual messaging events"""
    try:
        sender_id = messaging_event.get('sender', {}).get('id')
        recipient_id = messaging_event.get('recipient', {}).get('id')
        timestamp = messaging_event.get('timestamp')
        
        logging.info(f"Messaging event from {sender_id} to {recipient_id} at {timestamp}")
        
        # Handle different types of messaging events
        if 'message' in messaging_event:
            message = messaging_event['message']
            message_text = message.get('text', '')
            logging.info(f"Received message: {message_text}")
            
            # TODO: Implement your message handling logic here
            # Example: Store message, trigger automated responses, etc.
            
        elif 'postback' in messaging_event:
            postback = messaging_event['postback']
            payload = postback.get('payload', '')
            logging.info(f"Received postback: {payload}")
            
            # TODO: Implement your postback handling logic here
            
    except Exception as e:
        logging.error(f"Error handling messaging event: {str(e)}")

def handle_field_change(change, page_id):
    """Handle page field changes"""
    try:
        field = change.get('field')
        value = change.get('value')
        
        logging.info(f"Page {page_id} field '{field}' changed: {value}")
        
        # TODO: Implement your field change handling logic here
        # Example: Update local data, trigger notifications, etc.
        
    except Exception as e:
        logging.error(f"Error handling field change: {str(e)}")

def handle_user_change(change, user_id):
    """Handle user field changes"""
    try:
        field = change.get('field')
        value = change.get('value')
        
        logging.info(f"User {user_id} field '{field}' changed: {value}")
        
        # TODO: Implement your user change handling logic here
        # Example: Update user profile, sync with local database, etc.
        
    except Exception as e:
        logging.error(f"Error handling user change: {str(e)}")

@auth_bp.route('/facebook/fetch-posts', methods=['POST'])
@jwt_required()
def fetch_facebook_posts():
    """Fetch user's Facebook posts and save to database"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json() or {}
        limit = data.get('limit', 50)  # Default to 50 posts
        
        logging.info(f"Fetching Facebook posts for user {current_user_id}")
        
        result = FacebookService.fetch_user_posts(current_user_id, limit)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result), 200
        
    except Exception as e:
        logging.error(f"Error in fetch Facebook posts endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/facebook/posts', methods=['GET'])
@jwt_required()
def get_facebook_posts():
    """Get user's Facebook posts from database"""
    try:
        current_user_id = get_jwt_identity()
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        logging.info(f"Getting Facebook posts for user {current_user_id}")
        
        result = FacebookService.get_user_posts_from_db(current_user_id, limit, offset)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result), 200
        
    except Exception as e:
        logging.error(f"Error in get Facebook posts endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@auth_bp.route('/facebook/posts/<int:post_id>/fetch-comments', methods=['POST'])
@jwt_required()
def fetch_post_comments(post_id):
    """Fetch comments for a specific Facebook post"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json() or {}
        limit = data.get('limit', 25)  # Default to 25 comments
        
        # Verify the post belongs to the current user
        from ..models import FacebookPost
        post = FacebookPost.query.filter_by(id=post_id, user_id=current_user_id).first()
        if not post:
            return jsonify({'error': 'Post not found or unauthorized'}), 404
        
        # Get user's access token
        user = User.query.get(current_user_id)
        if not user or not user.facebook_access_token:
            return jsonify({'error': 'Facebook access token not found'}), 400
        
        logging.info(f"Fetching comments for post {post_id}")
        
        result = FacebookService.fetch_post_comments(post_id, user.facebook_access_token, limit)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result), 200
        
    except Exception as e:
        logging.error(f"Error in fetch post comments endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


