from flask import Blueprint, render_template, current_app, Response

main = Blueprint('main', __name__)

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