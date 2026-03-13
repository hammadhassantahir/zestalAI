import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models.phone_number import PhoneNumber
from ..services.twilio_service import TwilioService

logger = logging.getLogger(__name__)

sms_bp = Blueprint('sms', __name__)


@sms_bp.route('/send', methods=['POST'])
@jwt_required()
def send_sms():
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    to = data.get('to')
    body = data.get('body')

    if not to or not body:
        return jsonify({'error': 'to and body are required'}), 400

    # use the user's active phone number as sender
    phone = PhoneNumber.get_active_by_user(user_id)
    if not phone:
        return jsonify({'error': 'No active phone number assigned'}), 400

    twilio = TwilioService()
    result = twilio.send_sms(from_number=phone.phone_number, to_number=to, body=body)
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
    return jsonify(result), 201


@sms_bp.route('/send-bulk', methods=['POST'])
@jwt_required()
def send_bulk_sms():
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    recipients = data.get('recipients', [])
    body = data.get('body')

    if not recipients or not body:
        return jsonify({'error': 'recipients and body are required'}), 400
    if len(recipients) > 100:
        return jsonify({'error': 'Max 100 recipients per batch'}), 400

    phone = PhoneNumber.get_active_by_user(user_id)
    if not phone:
        return jsonify({'error': 'No active phone number assigned'}), 400

    twilio = TwilioService()
    results = []
    for to in recipients:
        r = twilio.send_sms(from_number=phone.phone_number, to_number=to, body=body)
        results.append({'to': to, 'success': 'error' not in r, 'sid': r.get('sid'), 'error': r.get('error')})

    sent = sum(1 for r in results if r['success'])
    return jsonify({'success': True, 'total': len(recipients), 'sent': sent, 'failed': len(recipients) - sent, 'results': results}), 201


@sms_bp.route('/<message_sid>', methods=['GET'])
@jwt_required()
def get_sms(message_sid):
    twilio = TwilioService()
    result = twilio.get_sms(message_sid)
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
    return jsonify(result), 200


@sms_bp.route('/history', methods=['GET'])
@jwt_required()
def list_sms():
    user_id = get_jwt_identity()
    limit = min(request.args.get('limit', 50, type=int), 200)

    phone = PhoneNumber.get_active_by_user(user_id)
    if not phone:
        return jsonify({'error': 'No active phone number assigned'}), 400

    twilio = TwilioService()
    result = twilio.list_sms(from_number=phone.phone_number, limit=limit)
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
    return jsonify(result), 200
