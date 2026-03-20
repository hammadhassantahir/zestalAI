import logging
from flask import Blueprint, request, jsonify, current_app
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

    phone = PhoneNumber.get_active_by_user(user_id)
    if not phone:
        return jsonify({'error': 'No active phone number assigned'}), 400

    # resolve language from recipient number
    from ..services.language_service import get_country_from_number, LANGUAGE_MAP
    _, region_code = get_country_from_number(to)
    language = LANGUAGE_MAP.get(region_code, {}).get('lang', 'en-US') if region_code else 'en-US'

    # generate translated content via Vapi
    try:
        from ..services.vapi_sms_service import VapiSmsService
        translated = VapiSmsService().generate(body, language)
    except Exception as e:
        logger.error(f"Vapi SMS generation error: {str(e)}")
        return jsonify({'error': f'SMS generation failed: {str(e)}'}), 502

    # test number override (language resolved from original `to`)
    send_to = current_app.config.get('SMS_TEST_NUMBER') or to

    status_callback = current_app.config['BASE_URL'] + '/api/webhooks/sms/status'

    # create log before sending so failures are also recorded
    from ..models.sms_log import SmsLog
    from ..extensions import db
    log = SmsLog(
        user_id=user_id,
        to_number=to,
        from_number=phone.phone_number,
        body=translated,
        language=language,
        status='queued',
    )
    db.session.add(log)
    db.session.commit()

    twilio = TwilioService()
    result = twilio.send_sms(
        from_number=phone.phone_number,
        to_number=send_to,
        body=translated,
        status_callback=status_callback,
    )

    if 'error' in result:
        log.status = 'failed'
        log.error_message = result['error']
        db.session.commit()
        return jsonify({'error': result['error']}), 400

    log.twilio_sid = result['sid']
    log.status = result.get('status', 'queued')
    db.session.commit()

    return jsonify({**result, 'language': language, 'log_id': log.id}), 201


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

    from ..services.language_service import get_country_from_number, LANGUAGE_MAP
    from ..services.vapi_sms_service import VapiSmsService
    from ..models.sms_log import SmsLog
    from ..extensions import db

    test_number = current_app.config.get('SMS_TEST_NUMBER')
    status_callback = current_app.config['BASE_URL'] + '/api/webhooks/sms/status'
    twilio = TwilioService()
    vapi_sms = VapiSmsService()
    results = []

    for to in recipients:
        _, region_code = get_country_from_number(to)
        language = LANGUAGE_MAP.get(region_code, {}).get('lang', 'en-US') if region_code else 'en-US'

        log = SmsLog(
            user_id=user_id,
            to_number=to,
            from_number=phone.phone_number,
            language=language,
            status='queued',
        )
        db.session.add(log)
        db.session.flush()

        try:
            translated = vapi_sms.generate(body, language)
        except Exception as e:
            log.status = 'failed'
            log.error_message = str(e)
            db.session.commit()
            results.append({'to': to, 'success': False, 'error': str(e), 'log_id': log.id})
            continue

        log.body = translated
        send_to = test_number or to
        r = twilio.send_sms(
            from_number=phone.phone_number,
            to_number=send_to,
            body=translated,
            status_callback=status_callback,
        )

        if 'error' in r:
            log.status = 'failed'
            log.error_message = r['error']
            db.session.commit()
            results.append({'to': to, 'success': False, 'error': r['error'], 'log_id': log.id})
        else:
            log.twilio_sid = r['sid']
            log.status = r.get('status', 'queued')
            db.session.commit()
            results.append({'to': to, 'success': True, 'sid': r['sid'], 'language': language, 'log_id': log.id})

    sent = sum(1 for r in results if r['success'])
    return jsonify({
        'success': True,
        'total': len(recipients),
        'sent': sent,
        'failed': len(recipients) - sent,
        'results': results,
    }), 201


@sms_bp.route('/logs', methods=['GET'])
@jwt_required()
def list_sms_logs():
    user_id = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    limit = min(request.args.get('limit', 20, type=int), 100)

    from ..models.sms_log import SmsLog
    query = SmsLog.query.filter_by(user_id=user_id).order_by(SmsLog.created_at.desc())
    total = query.count()
    logs = query.offset((page - 1) * limit).limit(limit).all()

    return jsonify({
        'success': True,
        'logs': [log.to_dict() for log in logs],
        'total': total,
        'page': page,
        'pages': (total + limit - 1) // limit,
    }), 200


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
