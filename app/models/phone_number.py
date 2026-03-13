from datetime import datetime
from ..extensions import db
import json


class PhoneNumber(db.Model):
    __tablename__ = 'phone_numbers'

    # Status constants
    STATUS_AVAILABLE = 'available'
    STATUS_ASSIGNED = 'assigned'
    STATUS_FROZEN = 'frozen'
    STATUS_RELEASED = 'released'
    STATUS_ERROR = 'error'

    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    twilio_sid = db.Column(db.String(50), unique=True, nullable=False)
    friendly_name = db.Column(db.String(255), nullable=True)
    country_code = db.Column(db.String(5), default='US')
    capabilities = db.Column(db.Text, nullable=True)  # JSON string
    status = db.Column(db.String(20), nullable=False, default=STATUS_AVAILABLE)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    assigned_at = db.Column(db.DateTime, nullable=True)
    vapi_phone_id = db.Column(db.String(100), nullable=True)
    display_name = db.Column(db.String(255), nullable=True)
    frozen_at = db.Column(db.DateTime, nullable=True)
    frozen_expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = db.relationship('User', backref='phone_numbers')

    def to_dict(self):
        capabilities_data = None
        if self.capabilities:
            try:
                capabilities_data = json.loads(self.capabilities)
            except (json.JSONDecodeError, TypeError):
                capabilities_data = self.capabilities

        return {
            'id': self.id,
            'phone_number': self.phone_number,
            'twilio_sid': self.twilio_sid,
            'friendly_name': self.friendly_name,
            'country_code': self.country_code,
            'capabilities': capabilities_data,
            'status': self.status,
            'user_id': self.user_id,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'vapi_phone_id': self.vapi_phone_id,
            'display_name': self.display_name,
            'frozen_at': self.frozen_at.isoformat() if self.frozen_at else None,
            'frozen_expires_at': self.frozen_expires_at.isoformat() if self.frozen_expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def get_available(cls, country_code=None):
        query = cls.query.filter_by(status=cls.STATUS_AVAILABLE)
        if country_code:
            query = query.filter_by(country_code=country_code)
        return query.first()

    @classmethod
    def get_by_user(cls, user_id):
        return cls.query.filter(
            cls.user_id == user_id,
            cls.status.in_([cls.STATUS_ASSIGNED, cls.STATUS_FROZEN])
        ).all()

    @classmethod
    def get_active_by_user(cls, user_id):
        return cls.query.filter_by(user_id=user_id, status=cls.STATUS_ASSIGNED).first()
