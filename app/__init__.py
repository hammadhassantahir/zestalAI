from flask import Flask
from .extensions import db, jwt, mail
from flask_migrate import Migrate
from .config import Config
from .auth.routes import auth_bp
from .main.routes import main
from .models.user import User

migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(main)
    
    return app