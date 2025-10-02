from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail

db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()

# Initialize scheduler service after other extensions are defined
def init_scheduler():
    from .services.scheduler_service import scheduler_service
    return scheduler_service

scheduler = None