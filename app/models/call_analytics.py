from datetime import datetime
from ..extensions import db
import json


class CallAnalytics(db.Model):
    __tablename__ = 'call_analytics'

    id = db.Column(db.Integer, primary_key=True)
    call_log_id = db.Column(db.Integer, db.ForeignKey('call_logs.id'), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sentiment = db.Column(db.String(20), nullable=True)
    interest_level = db.Column(db.Integer, nullable=True)
    objections = db.Column(db.Text, nullable=True)  # JSON list
    success_evaluation = db.Column(db.String(20), nullable=True)
    template_name = db.Column(db.String(100), nullable=True)
    extracted_data = db.Column(db.Text, nullable=True)  # JSON string
    extraction_status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    call_log = db.relationship('CallLog', backref=db.backref('analytics', uselist=False))
    user = db.relationship('User', backref='call_analytics')

    def to_dict(self):
        objections_data = None
        if self.objections:
            try:
                objections_data = json.loads(self.objections)
            except (json.JSONDecodeError, TypeError):
                objections_data = self.objections

        data = None
        if self.extracted_data:
            try:
                data = json.loads(self.extracted_data)
            except (json.JSONDecodeError, TypeError):
                data = self.extracted_data

        return {
            'id': self.id,
            'call_log_id': self.call_log_id,
            'user_id': self.user_id,
            'sentiment': self.sentiment,
            'interest_level': self.interest_level,
            'objections': objections_data,
            'success_evaluation': self.success_evaluation,
            'template_name': self.template_name,
            'extracted_data': data,
            'extraction_status': self.extraction_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
