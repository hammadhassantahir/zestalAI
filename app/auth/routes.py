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
        
        access_token = create_access_token(identity=user.id)
        
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
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'user': user.to_dict()
        }), 201
    except Exception as e:
        logging.error(f"Error in signup: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

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
