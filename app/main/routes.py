from flask import Blueprint, render_template, current_app, jsonify

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return jsonify({'message': 'Test. Welcome to the ZestalAI Auth API.'}), 201


@main.route('/facebook-login')
def facebook_login_page():
    return render_template('facebook_login.html', 
                         facebook_client_id=current_app.config['FACEBOOK_CLIENT_ID'])