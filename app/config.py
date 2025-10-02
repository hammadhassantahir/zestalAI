import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Base URL for email links
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
    
    # Frontend URL for OAuth redirects
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:3001').split(',')
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # Mail Configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    
    # Facebook OAuth Configuration
    FACEBOOK_CLIENT_ID = os.getenv('FACEBOOK_CLIENT_ID')
    FACEBOOK_CLIENT_SECRET = os.getenv('FACEBOOK_CLIENT_SECRET')
    FACEBOOK_OAUTH_REDIRECT_URI = os.getenv('FACEBOOK_OAUTH_REDIRECT_URI')
    
    # Facebook App Configuration (for token refresh)
    FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID', FACEBOOK_CLIENT_ID)
    FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET', FACEBOOK_CLIENT_SECRET)
    
    # Facebook Webhook Configuration
    FACEBOOK_WEBHOOK_VERIFY_TOKEN = os.getenv('FACEBOOK_WEBHOOK_VERIFY_TOKEN')

    # GoHighLevel API Key
    GHL_ACCESS_TOKEN = os.getenv('GHL_ACCESS_TOKEN')
    GHL_LOCATION_ID = os.getenv('GHL_LOCATION_ID')
    GHL_COMPANY_ID = os.getenv('GHL_COMPANY_ID')

    GHL_API_KEY = os.getenv('GHL_API_KEY')
    GHL_CLIENT_ID = os.getenv('GHL_CLIENT_ID')
    GHL_CLIENT_SECRET = os.getenv('GHL_CLIENT_SECRET')
    GHL_REDIRECT_URI = os.getenv('GHL_REDIRECT_URI')