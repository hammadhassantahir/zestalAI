import json
import logging
from datetime import time
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.user_call_config import UserCallConfig
from ..services.language_service import SUPPORTED_LANGUAGES
from ..services.call_script_templates import list_templates, DEFAULT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

config_bp = Blueprint('config', __name__)


@config_bp.route('/call', methods=['GET'])
@jwt_required()
def get_call_config():
    user_id = get_jwt_identity()
    cfg = UserCallConfig.query.filter_by(user_id=user_id).first()
    if not cfg:
        return jsonify({'config': None, 'default_system_prompt': DEFAULT_SYSTEM_PROMPT}), 200
    return jsonify({'config': cfg.to_dict(), 'default_system_prompt': DEFAULT_SYSTEM_PROMPT}), 200


@config_bp.route('/call', methods=['PUT'])
@jwt_required()
def upsert_call_config():
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    cfg = UserCallConfig.query.filter_by(user_id=user_id).first()
    is_new = cfg is None
    if not cfg:
        cfg = UserCallConfig(user_id=user_id)
        db.session.add(cfg)

    # seed default prompt for new configs if not explicitly provided
    if is_new and 'system_prompt_base' not in data:
        cfg.system_prompt_base = DEFAULT_SYSTEM_PROMPT

    # simple string fields
    for field in ['tone', 'default_language', 'fallback_language',
                  'greeting_template', 'system_prompt_base',
                  'voice_provider', 'voice_id', 'call_window_timezone',
                  'active_template']:
        if field in data:
            setattr(cfg, field, data[field])

    # JSON fields — serialize to string
    for field in ['language_overrides', 'greeting_presets', 'call_window_days']:
        if field in data:
            val = data[field]
            setattr(cfg, field, json.dumps(val) if val is not None else None)

    # time fields
    for field in ['call_window_start', 'call_window_end']:
        if field in data:
            val = data[field]
            setattr(cfg, field, time.fromisoformat(val) if val else None)

    # bool
    if 'is_active' in data:
        cfg.is_active = data['is_active']

    try:
        db.session.commit()
        return jsonify({'success': True, 'config': cfg.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"upsert_call_config error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@config_bp.route('/call/languages', methods=['GET'])
@jwt_required()
def get_languages():
    return jsonify({'languages': SUPPORTED_LANGUAGES}), 200


@config_bp.route('/call/voices', methods=['GET'])
@jwt_required()
def get_voices():
    voices = [
        {'provider': 'openai', 'voice_id': 'alloy', 'name': 'Alloy', 'gender': 'neutral'},
        {'provider': 'openai', 'voice_id': 'echo', 'name': 'Echo', 'gender': 'male'},
        {'provider': 'openai', 'voice_id': 'fable', 'name': 'Fable', 'gender': 'male'},
        {'provider': 'openai', 'voice_id': 'onyx', 'name': 'Onyx', 'gender': 'male'},
        {'provider': 'openai', 'voice_id': 'nova', 'name': 'Nova', 'gender': 'female'},
        {'provider': 'openai', 'voice_id': 'shimmer', 'name': 'Shimmer', 'gender': 'female'},
    ]
    return jsonify({'voices': voices}), 200


@config_bp.route('/call/greeting-presets', methods=['GET'])
@jwt_required()
def get_greeting_presets():
    presets = [
        {'id': 'professional', 'text': 'Hello {name}, this is {company}. Do you have a moment to speak?'},
        {'id': 'casual', 'text': 'Hi {name}! This is {company} calling. Got a quick minute?'},
        {'id': 'follow_up', 'text': "Hi {name}, I'm following up from {company}. Is this a good time?"},
    ]
    return jsonify({'presets': presets}), 200


@config_bp.route('/call/templates', methods=['GET'])
@jwt_required()
def get_templates():
    return jsonify({'templates': list_templates()}), 200
