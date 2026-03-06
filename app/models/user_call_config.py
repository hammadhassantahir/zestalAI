from datetime import datetime
from ..extensions import db
import json


class UserCallConfig(db.Model):
    __tablename__ = 'user_call_configs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    tone = db.Column(db.String(20), default='formal')
    default_language = db.Column(db.String(10), default='en-US')
    fallback_language = db.Column(db.String(10), default='en-US')
    language_overrides = db.Column(db.Text, nullable=True)  # JSON string
    greeting_template = db.Column(db.Text, nullable=True)
    greeting_presets = db.Column(db.Text, nullable=True)  # JSON array
    system_prompt_base = db.Column(db.Text, nullable=True)
    voice_provider = db.Column(db.String(50), default='openai')
    voice_id = db.Column(db.String(100), nullable=True)
    call_window_start = db.Column(db.Time, nullable=True)
    call_window_end = db.Column(db.Time, nullable=True)
    call_window_days = db.Column(db.Text, nullable=True)  # JSON array
    call_window_timezone = db.Column(db.String(50), default='UTC')
    active_template = db.Column(db.String(100), default='lead_qualification')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = db.relationship('User', backref=db.backref('call_config', uselist=False))

    def to_dict(self):
        overrides = None
        if self.language_overrides:
            try:
                overrides = json.loads(self.language_overrides)
            except (json.JSONDecodeError, TypeError):
                overrides = self.language_overrides

        presets = None
        if self.greeting_presets:
            try:
                presets = json.loads(self.greeting_presets)
            except (json.JSONDecodeError, TypeError):
                presets = self.greeting_presets

        days = None
        if self.call_window_days:
            try:
                days = json.loads(self.call_window_days)
            except (json.JSONDecodeError, TypeError):
                days = self.call_window_days

        return {
            'id': self.id,
            'user_id': self.user_id,
            'tone': self.tone,
            'default_language': self.default_language,
            'fallback_language': self.fallback_language,
            'language_overrides': overrides,
            'greeting_template': self.greeting_template,
            'greeting_presets': presets,
            'system_prompt_base': self.system_prompt_base,
            'voice_provider': self.voice_provider,
            'voice_id': self.voice_id,
            'call_window_start': self.call_window_start.strftime('%H:%M') if self.call_window_start else None,
            'call_window_end': self.call_window_end.strftime('%H:%M') if self.call_window_end else None,
            'call_window_days': days,
            'call_window_timezone': self.call_window_timezone,
            'active_template': self.active_template,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
