from flask import Blueprint, render_template, current_app, Response, request
from app.script.goHighLevel import GoHighLevelAPI, GoHighLevelError, RateLimitError
import requests
import json


main = Blueprint('main', __name__)

@main.route('/ghlRedirects')
def ghlRedirects():
    data = request.get_json()
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


@main.route('/ghl')
def ghl():
    contacts = []
    ghl = GoHighLevelAPI(current_app.config['GHL_API_KEY'])
    try:
        # ✅ Get first 5 contacts
        contacts = ghl.get_contacts(limit=20)
        print("Contacts:", contacts)

        # ✅ Create a new contact
        # new_contact = ghl.create_contact({"firstName": "Alice", "lastName": "Smith", "email": "alice.smith@example.com"})
        # print("New Contact:", new_contact)
    except RateLimitError as e:
        print("Hit API rate limit:", e)

    except GoHighLevelError as e:
        print("API Error:", e)

    except Exception as e:
        print(f"Error in ghl: {e}")

    return render_template('test.html', contacts=contacts)
