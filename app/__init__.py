from flask import Flask, jsonify, request
from flask_cors import CORS
from .extensions import db, jwt, mail
from flask_migrate import Migrate
from .config import Config
from .auth.routes import auth_bp
from .main.routes import main
from .models.user import User
import logging

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
         resources={r"*": {
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
    
    # Error handler for all exceptions
    @app.errorhandler(Exception)
    def handle_error(error):
        logging.error(f"Unhandled error: {str(error)}")
        return jsonify({'error': 'Internal server error'}), 500
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main)
    
    return app