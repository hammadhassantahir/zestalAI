from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from ..extensions import db
from ..models.user import User
from ..services.email_service import send_verification_email, send_reset_password_email
import secrets
import requests

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
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
    
    # Send verification email
    # send_verification_email(user)
    
    return jsonify({'message': 'User registered successfully. Please check your email for verification.'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if not user.is_verified:
        return jsonify({'error': 'Please verify your email first'}), 403
    
    access_token = create_access_token(identity=user.id)
    return jsonify({
        'access_token': access_token,
        'user': user.to_dict()
    })

@auth_bp.route('/verify/<code>', methods=['GET'])
def verify_email(code):
    user = User.query.filter_by(code=code).first()
    if not user:
        return jsonify({'error': 'Invalid verification code'}), 400
    
    user.is_verified = True
    user.code = None
    db.session.commit()
    
    return jsonify({'message': 'Email verified successfully'})

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'If an account exists with this email, a reset link will be sent.'}), 200
    
    # Generate reset code
    user.code = secrets.token_urlsafe(32)
    db.session.commit()
    
    # Send reset email
    send_reset_password_email(user)
    
    return jsonify({'message': 'Password reset instructions have been sent to your email.'}), 200

@auth_bp.route('/reset-password', methods=['POST'])
@jwt_required()
def reset_password():
    data = request.get_json()
    current_user_id = get_jwt_identity()
    
    if not data.get('new_password'):
        return jsonify({'error': 'New password is required'}), 400
    
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    user.set_password(data['new_password'])
    db.session.commit()
    
    return jsonify({'message': 'Password has been reset successfully'})

@auth_bp.route('/facebook/login', methods=['POST'])
def facebook_login():
    data = request.get_json()
    access_token = data.get('access_token')
    
    if not access_token:
        return jsonify({'error': 'Facebook access token is required'}), 400
    
    try:
        # Verify token with Facebook
        fb_response = requests.get(
            'https://graph.facebook.com/me',
            params={
                'fields': 'id,first_name,last_name,email',
                'access_token': access_token
            }
        )
        fb_data = fb_response.json()
        
        if 'error' in fb_data:
            return jsonify({'error': 'Invalid Facebook token'}), 401
        
        # Check if user exists
        user = User.query.filter_by(facebook_id=fb_data['id']).first()
        if not user:
            # Check if email exists
            user = User.query.filter_by(email=fb_data.get('email')).first()
            if user:
                # Link Facebook ID to existing account
                user.facebook_id = fb_data['id']
            else:
                # Create new user
                user = User(
                    first_name=fb_data.get('first_name'),
                    last_name=fb_data.get('last_name'),
                    email=fb_data.get('email'),
                    facebook_id=fb_data['id'],
                    is_verified=True  # Facebook users are pre-verified
                )
                db.session.add(user)
        
        db.session.commit()
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': 'Failed to authenticate with Facebook'}), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_user_details():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    if not user.is_verified:
        return jsonify({'error': 'Please verify your email first'}), 403
    
    return jsonify(user.to_dict())