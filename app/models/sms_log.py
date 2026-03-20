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

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'to_number': self.to_number,
            'from_number': self.from_number,
            'body': self.body,
            'language': self.language,
            'twilio_sid': self.twilio_sid,
            'status': self.status,
            'error_code': self.error_code,
            'error_message': self.error_message,
            'is_valid_number': self.is_valid_number,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
