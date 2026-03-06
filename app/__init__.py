from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from .extensions import db, jwt, mail, init_scheduler
from flask_migrate import Migrate
from .config import Config
from .auth.routes import auth_bp
from .main.routes import main
from .ghl.routes import ghl
from .scheduler.routes import scheduler_bp
from .models.user import User
import logging
import requests
import json
from functools import wraps
import os

migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Enable CORS - Production-ready configuration
    CORS(app, 
         resources={r"/api/*": {
             "origins": app.config['CORS_ORIGINS'],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization"],
             "expose_headers": ["Content-Type", "Authorization"],
             "supports_credentials": True,
             "max_age": 600
         }},
         supports_credentials=True
    )
    
    # Alternative: For development/testing, you can allow all origins
    # Uncomment the line below and comment out the CORS configuration above
    # CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=False)
    
    # Additional CORS headers for preflight requests
    @app.after_request
    def add_cors_headers(response):
        # Always add CORS headers for API routes
        if request.path.startswith('/api/'):
            origin = request.headers.get('Origin')
            if origin:
                # Check if origin is in allowed list
                allowed_origins = app.config['CORS_ORIGINS']
                if origin in allowed_origins:
                    response.headers['Access-Control-Allow-Origin'] = origin
                else:
                    # Log unauthorized origin for debugging
                    logging.warning(f"Unauthorized origin: {origin}. Allowed: {allowed_origins}")
                    response.headers['Access-Control-Allow-Origin'] = allowed_origins[0]
            else:
                response.headers['Access-Control-Allow-Origin'] = app.config['CORS_ORIGINS'][0]
            
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            response.headers['Access-Control-Max-Age'] = '600'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            
            # Handle preflight requests
            if request.method == 'OPTIONS':
                response.status_code = 200
        
        return response
    
    # Handle Socket.IO requests directly on the main app (not blueprint)
    @app.before_request
    def handle_socketio_requests():
        """Handle Socket.IO requests before they hit route handlers"""
        if request.path.startswith('/socket.io'):
            return Response(status=200)
    
    # Error handler for 404 errors
    @app.errorhandler(404)
    def handle_404(error):
        # Log the requested URL to help identify what's causing 404s
        requested_url = request.url
        logging.warning(f"404 Not Found: {request.method} {requested_url} from {request.remote_addr}")
        return jsonify({'error': 'Not Found'}), 404
    
    # Error handler for all other exceptions
    @app.errorhandler(Exception)
    def handle_error(error):
        logging.error(f"Unhandled error: {str(error)}")
        return jsonify({'error': 'Internal server error'}), 500
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize scheduler
    scheduler = init_scheduler()
    scheduler.init_app(app)
    
    # Validate required env vars for phone/calling features
    _required_phone_vars = ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'VAPI_API_KEY', 'VAPI_WEBHOOK_URL']
    _missing = [v for v in _required_phone_vars if not app.config.get(v)]
    if _missing:
        logging.warning(f"Phone/calling features disabled — missing env vars: {', '.join(_missing)}")

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(main, url_prefix='/api')
    app.register_blueprint(ghl, url_prefix='/api/ghl')
    app.register_blueprint(scheduler_bp, url_prefix='/api/scheduler')
    
    # Register Facebook sync blueprint
    from .facebook import facebook_bp
    app.register_blueprint(facebook_bp, url_prefix='/api/facebook')

    # Register Phone pool blueprint
    from .phone import phone_bp
    app.register_blueprint(phone_bp, url_prefix='/api/phone')

    # Register Calls blueprint
    from .calls import calls_bp
    app.register_blueprint(calls_bp, url_prefix='/api/calls')

    # Register Webhooks blueprint
    from .webhooks import webhooks_bp
    app.register_blueprint(webhooks_bp, url_prefix='/api/webhooks')

    # Register Analytics blueprint
    from .analytics import analytics_bp
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')

    # Register Config blueprint
    from .config_routes import config_bp
    app.register_blueprint(config_bp, url_prefix='/api/config')
    
    # Start scheduler after all extensions are initialized
    # Only start scheduler in the main process (not in reloader process)
    # This prevents duplicate scheduler instances in debug mode
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        with app.app_context():
            scheduler.start()
            logging.info("Scheduler started successfully")
    else:
        logging.info("Skipping scheduler start in reloader process")
    
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.WARNING)
    return app