from datetime import datetime
from ..extensions import db

INVALID_NUMBER_CODES = {30003, 30005, 30006}

class SmsLog(db.Model):
    __tablename__ = 'sms_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    to_number = db.Column(db.String(20), nullable=False)
    from_number = db.Column(db.String(20), nullable=False)
    body = db.Column(db.Text, nullable=True)
    language = db.Column(db.String(10), nullable=True)
    twilio_sid = db.Column(db.String(50), nullable=True, index=True)
    status = db.Column(db.String(20), nullable=False, default='queued')
    error_code = db.Column(db.String(10), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    is_valid_number = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='sms_logs')
