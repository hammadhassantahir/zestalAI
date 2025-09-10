from flask import Blueprint

bp = Blueprint('ghl', __name__)


from app.ghl import routes
