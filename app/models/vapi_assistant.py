from datetime import datetime
from ..extensions import db
import json


class VapiAssistant(db.Model):
    __tablename__ = 'vapi_assistants'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vapi_assistant_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    model_provider = db.Column(db.String(50), default='openai')
    model_name = db.Column(db.String(100), default='gpt-4o')
    voice_provider = db.Column(db.String(50), nullable=True)
    voice_id = db.Column(db.String(100), nullable=True)
    first_message = db.Column(db.Text, nullable=True)
    system_prompt = db.Column(db.Text, nullable=True)
    tools = db.Column(db.Text, nullable=True)  # JSON string
    template_name = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = db.relationship('User', backref='vapi_assistants')

    def to_dict(self):
        tools_data = None
        if self.tools:
            try:
                tools_data = json.loads(self.tools)
            except (json.JSONDecodeError, TypeError):
                tools_data = self.tools

        return {
            'id': self.id,
            'user_id': self.user_id,
            'vapi_assistant_id': self.vapi_assistant_id,
            'name': self.name,
            'model_provider': self.model_provider,
            'model_name': self.model_name,
            'voice_provider': self.voice_provider,
            'voice_id': self.voice_id,
            'first_message': self.first_message,
            'system_prompt': self.system_prompt,
            'tools': tools_data,
            'template_name': self.template_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
