from datetime import datetime
from ..extensions import db
import json


class CallLog(db.Model):
    __tablename__ = 'call_logs'

    # Status constants
    STATUS_QUEUED = 'queued'
    STATUS_RINGING = 'ringing'
    STATUS_IN_PROGRESS = 'in-progress'
    STATUS_ENDED = 'ended'
    STATUS_FAILED = 'failed'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vapi_call_id = db.Column(db.String(100), unique=True, nullable=False)
    assistant_id = db.Column(db.Integer, db.ForeignKey('vapi_assistants.id'), nullable=True)
    phone_number_id = db.Column(db.Integer, db.ForeignKey('phone_numbers.id'), nullable=True)
    direction = db.Column(db.String(20), default='outbound')
    customer_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(30), nullable=False, default=STATUS_QUEUED)
    end_reason = db.Column(db.String(50), nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    ended_at = db.Column(db.DateTime, nullable=True)
    duration_seconds = db.Column(db.Integer, nullable=True)
    transcript = db.Column(db.Text, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    structured_data = db.Column(db.Text, nullable=True)  # JSON string
    recording_url = db.Column(db.Text, nullable=True)
    cost = db.Column(db.Float, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    lead_context = db.Column(db.Text, nullable=True)  # JSON string
    template_used = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='call_logs')
    assistant = db.relationship('VapiAssistant', backref='call_logs')
    phone_number = db.relationship('PhoneNumber', backref='call_logs')

    def to_dict(self):
        lead_ctx = None
        if self.lead_context:
            try:
                lead_ctx = json.loads(self.lead_context)
            except (json.JSONDecodeError, TypeError):
                lead_ctx = self.lead_context

        structured = None
        if self.structured_data:
            try:
                structured = json.loads(self.structured_data)
            except (json.JSONDecodeError, TypeError):
                structured = self.structured_data

        return {
            'id': self.id,
            'user_id': self.user_id,
            'vapi_call_id': self.vapi_call_id,
            'assistant_id': self.assistant_id,
            'phone_number_id': self.phone_number_id,
            'direction': self.direction,
            'customer_number': self.customer_number,
            'status': self.status,
            'end_reason': self.end_reason,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'duration_seconds': self.duration_seconds,
            'transcript': self.transcript,
            'summary': self.summary,
            'structured_data': structured,
            'recording_url': self.recording_url,
            'cost': self.cost,
            'error_message': self.error_message,
            'lead_context': lead_ctx,
            'template_used': self.template_used,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
