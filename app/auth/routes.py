from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from ..extensions import db
from ..models.user import User
from ..services.email_service import send_verification_email, send_reset_password_email
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
        fb_user_info = verify_facebook_token(access_token)
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
            # Update Facebook ID if not set
            if not user.facebook_id:
                user.facebook_id = facebook_id
                db.session.commit()
        else:
            # Create new user
            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                facebook_id=facebook_id,
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
    """Verify Facebook access token and return user info"""
    try:
        # First verify the token's validity
        debug_url = f"https://graph.facebook.com/debug_token?input_token={access_token}&access_token={access_token}"
        debug_response = requests.get(debug_url, timeout=10)
        debug_data = debug_response.json()
        
        logging.info(f"Token debug response: {debug_data}")
        
        if not debug_response.ok or not debug_data.get('data', {}).get('is_valid'):
            logging.error(f"Invalid Facebook token: {debug_data}")
            return None
            
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
                return None
                
            return user_data
        else:
            logging.error(f"Facebook API error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Error verifying Facebook token: {str(e)}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error verifying Facebook token: {str(e)}")
        return None

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
