from flask import Blueprint, render_template, current_app, Response, request, jsonify
from app.script.goHighLevel import GoHighLevelAPI
from app.script.goHighLevelV2 import GoHighLevelAPI as GoHighLevelV2API
import requests
import json
import os
from functools import wraps


main = Blueprint('main', __name__)

def get_ghl_client():
    """Get an instance of GoHighLevel V2 API client."""
    return GoHighLevelV2API(
        client_id=current_app.config['GHL_CLIENT_ID'],
        client_secret=current_app.config['GHL_CLIENT_SECRET'],
        redirect_uri=current_app.config['GHL_REDIRECT_URI']
    )

def require_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ghl_client = get_ghl_client()
        if not ghl_client.access_token:
            return jsonify({"error": "No access token. Please authenticate first."}), 401
        return f(*args, **kwargs)
    return decorated_function

# https://app.zestal.pro/api/ghlRedirects
@main.route('/ghlRedirects')
def ghlRedirects():
    data = request.get_json()
    print('***************************************************')
    print(data)
    return Response(status=200)


@main.route('/zestal/webhook', methods=['POST'])
def zestal_webhook():
    data = request.get_json()
    fileName = 'zestal_webhook.json'
    filePath = os.path.join(current_app.root_path, 'static', fileName)
    if os.path.exists(filePath):
        with open(filePath, 'r') as f:
            try:
                existing_data = json.load(f)
                if isinstance(existing_data, dict):
                    existing_data = [existing_data]
            except json.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    existing_data.append(data)

    with open(filePath, 'w') as f:
        json.dump(existing_data, f, indent=4)
    print('***************************************************')
    print(data)
    return Response(status=200)


@main.route('/facebook-login')
def facebook_login_page():
    return render_template('facebook_login.html', 
                         facebook_client_id=current_app.config['FACEBOOK_CLIENT_ID'])

@main.route('/socket.io/')
def handle_socketio():
    """Handle socket.io requests to prevent 404 logs"""
    return Response(status=200)

@main.route('/')
def index():
    return "Welcome to ZestalAI Auth API"


# GoHighLevel V2 API Routes

@main.route('/ghlcallback')
def ghl_callback():
    """Handle the OAuth callback from GoHighLevel."""
    code = request.args.get('code')
    error = request.args.get('error')
    error_description = request.args.get('error_description')

    print(f"Callback received with full URL: {request.url}")  # Debug full URL
    print(f"Callback received - Code: {code}, Error: {error}, Description: {error_description}")
    print(f"All args: {request.args}")
    print(f"Headers: {dict(request.headers)}")  # Debug headers

    if error:
        return jsonify({
            "error": error,
            "error_description": error_description
        }), 400

    if not code:
        return jsonify({"error": "No authorization code received"}), 400

    try:
        ghl_client = get_ghl_client()
        print(f"Client configuration: ID={ghl_client.client_id}, Redirect={ghl_client.redirect_uri}")  # Debug config
        
        # Exchange the code for tokens
        token_data = ghl_client.exchange_code_for_token(code)
        
        # Store the tokens in the session or database for future use
        # For now, we'll just return them (in production, you should store these securely)
        return jsonify({
            "message": "Authorization successful!",
            "token_data": token_data
        })
    except Exception as e:
        print(f"Error in callback: {str(e)}")  # Add debug logging
        print(f"Full error details: {repr(e)}")  # More detailed error info
        return jsonify({
            "error": "Token exchange failed",
            "details": str(e),
            "type": type(e).__name__
        }), 500

@main.route('/ghl/auth')
def ghl_auth():
    """Get the authorization URL for GoHighLevel OAuth."""
    ghl_client = get_ghl_client()
    auth_url = ghl_client.get_auth_url()
    return jsonify({
        "auth_url": auth_url,
        "message": "Please visit this URL to authorize the application"
    })

@main.route('/ghl/contacts')
@require_token
def get_contacts():
    """Get contacts from GoHighLevel."""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 100, type=int)
        ghl_client = get_ghl_client()
        contacts = ghl_client.get_contacts(limit=limit, page=page)
        return jsonify(contacts)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/ghl/appointments')
@require_token
def get_appointments():
    """Get appointments from GoHighLevel."""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 100, type=int)
        ghl_client = get_ghl_client()
        appointments = ghl_client.get_appointments(limit=limit, page=page)
        return jsonify(appointments)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main.route('/ghl/conversations')
@require_token
def get_conversations():
    """Get conversations from GoHighLevel."""
    try:
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 100, type=int)
        ghl_client = get_ghl_client()
        conversations = ghl_client.get_conversations(limit=limit, page=page)
        return jsonify(conversations)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Example route showing how to use the API with error handling
@main.route('/ghl/dashboard')
@require_token
def ghl_dashboard():
    """Get an overview of GoHighLevel data."""
    try:
        ghl_client = get_ghl_client()
        # Get multiple types of data
        contacts = ghl_client.get_contacts(limit=5)
        appointments = ghl_client.get_appointments(limit=5)
        conversations = ghl_client.get_conversations(limit=5)
        
        return jsonify({
            "contacts": contacts,
            "appointments": appointments,
            "conversations": conversations,
            "status": "success"
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500


# @main.route('/ghl')
# def ghl():
#     contacts = []
#     ghl = GoHighLevelAPI(current_app.config['GHL_API_KEY'])
#     try:
#         # ✅ Get first 5 contacts
#         contacts = ghl.get_contacts(limit=20)
#         print("Contacts:", contacts)
#         # ✅ Create a new contact
#         # new_contact = ghl.create_contact({"firstName": "Alice", "lastName": "Smith", "email": "alice.smith@example.com"})
#         # print("New Contact:", new_contact)
#     except RateLimitError as e:
#         print("Hit API rate limit:", e)   