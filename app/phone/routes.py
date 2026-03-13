import io
import csv
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.phone_number import PhoneNumber
from ..models.call_log import CallLog
from ..services.twilio_service import TwilioService
from ..services.phone_pool_service import PhonePoolService

logger = logging.getLogger(__name__)

phone_bp = Blueprint('phone', __name__)


# ─── Admin Routes ───────────────────────────────────────────────────────────


@phone_bp.route('/admin/search', methods=['POST'])
@jwt_required()
def admin_search_numbers():
    # TODO: Add admin role check
    data = request.get_json() or {}
    country_code = data.get('country_code', 'US')
    area_code = data.get('area_code')
    limit = min(data.get('limit', 10), 50)

    twilio = TwilioService()
    result = twilio.search_available_numbers(
        country_code=country_code,
        area_code=area_code,
        limit=limit,
    )
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
    return jsonify(result), 200


@phone_bp.route('/admin/buy', methods=['POST'])
@jwt_required()
def admin_buy_number():
    # TODO: Add admin role check
    data = request.get_json() or {}
    phone_number = data.get('phone_number')
    country_code = data.get('country_code', 'US')

    if not phone_number:
        return jsonify({'error': 'phone_number is required'}), 400

    result = PhonePoolService.buy_and_add_to_pool(phone_number, country_code)
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
    return jsonify(result), 201


@phone_bp.route('/admin/pool', methods=['GET'])
@jwt_required()
def admin_list_pool():
    # TODO: Add admin role check
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 200)

    query = PhoneNumber.query
    if status:
        query = query.filter_by(status=status)
    query = query.order_by(PhoneNumber.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'phone_numbers': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
    }), 200


@phone_bp.route('/admin/pool/stats', methods=['GET'])
@jwt_required()
def admin_pool_stats():
    # TODO: Add admin role check
    result = PhonePoolService.get_pool_stats()
    if 'error' in result:
        return jsonify({'error': result['error']}), 500
    return jsonify(result), 200


@phone_bp.route('/admin/<int:phone_id>/release', methods=['DELETE'])
@jwt_required()
def admin_release_number(phone_id):
    # TODO: Add admin role check
    result = PhonePoolService.release_and_remove(phone_id)
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
    return jsonify(result), 200


@phone_bp.route('/admin/<int:phone_id>/assign', methods=['POST'])
@jwt_required()
def admin_assign_number(phone_id):
    # TODO: Add admin role check
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    result = PhonePoolService.assign_to_user(phone_id, user_id)
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
    return jsonify(result), 200


@phone_bp.route('/admin/<int:phone_id>/unassign', methods=['POST'])
@jwt_required()
def admin_unassign_number(phone_id):
    # TODO: Add admin role check
    result = PhonePoolService.unassign(phone_id)
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
    return jsonify(result), 200


@phone_bp.route('/admin/auto-assign', methods=['POST'])
@jwt_required()
def admin_auto_assign():
    # TODO: Add admin role check
    data = request.get_json() or {}
    user_id = data.get('user_id')
    country_code = data.get('country_code')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400

    result = PhonePoolService.auto_assign_to_user(user_id, country_code)
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
    return jsonify(result), 200


@phone_bp.route('/admin/sync-twilio', methods=['POST'])
@jwt_required()
def admin_sync_twilio():
    result = PhonePoolService.sync_from_twilio()
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
    return jsonify(result), 200


@phone_bp.route('/admin/<int:phone_id>/retry-vapi-import', methods=['POST'])
@jwt_required()
def admin_retry_vapi_import(phone_id):
    # TODO: Add admin role check
    result = PhonePoolService.retry_vapi_import(phone_id)
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
    return jsonify(result), 200


# ─── User Routes ────────────────────────────────────────────────────────────


@phone_bp.route('/my-numbers', methods=['GET'])
@jwt_required()
def my_numbers():
    user_id = get_jwt_identity()
    numbers = PhoneNumber.get_by_user(user_id)
    return jsonify({'phone_numbers': [n.to_dict() for n in numbers]}), 200


@phone_bp.route('/my-numbers/<int:phone_id>', methods=['PUT'])
@jwt_required()
def update_number(phone_id):
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    phone = PhoneNumber.query.filter(
        PhoneNumber.id == phone_id,
        PhoneNumber.user_id == user_id,
        PhoneNumber.status.in_([PhoneNumber.STATUS_ASSIGNED, PhoneNumber.STATUS_FROZEN])
    ).first()
    if not phone:
        return jsonify({'error': 'Phone number not found'}), 404

    if 'display_name' in data:
        phone.display_name = data['display_name']
        db.session.commit()

    return jsonify({'success': True, 'phone_number': phone.to_dict()}), 200


@phone_bp.route('/my-numbers/<int:phone_id>', methods=['DELETE'])
@jwt_required()
def freeze_number(phone_id):
    user_id = get_jwt_identity()
    result = PhonePoolService.freeze_number(phone_id, user_id)
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
    return jsonify(result), 200


@phone_bp.route('/my-numbers/<int:phone_id>/restore', methods=['POST'])
@jwt_required()
def restore_number(phone_id):
    user_id = get_jwt_identity()
    result = PhonePoolService.restore_number(phone_id, user_id)
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
    return jsonify(result), 200


@phone_bp.route('/my-numbers/<int:phone_id>/export-logs', methods=['GET'])
@jwt_required()
def export_call_logs(phone_id):
    user_id = get_jwt_identity()

    phone = PhoneNumber.query.filter(
        PhoneNumber.id == phone_id,
        PhoneNumber.user_id == user_id,
        PhoneNumber.status.in_([PhoneNumber.STATUS_ASSIGNED, PhoneNumber.STATUS_FROZEN])
    ).first()
    if not phone:
        return jsonify({'error': 'Phone number not found'}), 404

    logs = CallLog.query.filter_by(
        user_id=user_id,
        phone_number_id=phone_id,
    ).order_by(CallLog.created_at.desc()).all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['id', 'customer_number', 'direction', 'status', 'duration_seconds',
                     'template_used', 'created_at', 'summary'])
    for log in logs:
        writer.writerow([
            log.id, log.customer_number, log.direction, log.status,
            log.duration_seconds or '', log.template_used or '',
            log.created_at.isoformat() if log.created_at else '',
            (log.summary or '').replace('\n', ' '),
        ])

    return Response(
        buf.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=call_logs_phone_{phone_id}.csv'}
    )


@phone_bp.route('/available', methods=['GET'])
@jwt_required()
def search_available():
    country_code = request.args.get('country_code', 'US')
    area_code = request.args.get('area_code')
    limit = min(request.args.get('limit', 10, type=int), 20)

    twilio = TwilioService()
    result = twilio.search_available_numbers(
        country_code=country_code,
        area_code=area_code,
        limit=limit,
    )
    if 'error' in result:
        return jsonify({'error': result['error']}), 400
    return jsonify(result), 200


@phone_bp.route('/purchase', methods=['POST'])
@jwt_required()
def purchase_number():
    user_id = get_jwt_identity()
    data = request.get_json() or {}
    phone_number = data.get('phone_number')
    country_code = data.get('country_code', 'US')
    display_name = data.get('display_name')

    if not phone_number:
        return jsonify({'error': 'phone_number is required'}), 400

    # only 1 active number per user (frozen don't count)
    active = PhoneNumber.get_active_by_user(user_id)
    if active:
        return jsonify({'error': 'You already have an active number. Freeze it first.'}), 400

    from ..models.user import User
    user = User.query.get(user_id)
    vapi_tag = f"{user_id}-{user.first_name} {user.last_name}"
    result = PhonePoolService.buy_and_add_to_pool(phone_number, country_code, vapi_name=vapi_tag)
    if 'error' in result:
        return jsonify({'error': result['error']}), 400

    phone = PhoneNumber.query.filter_by(phone_number=phone_number).first()
    phone.status = PhoneNumber.STATUS_ASSIGNED
    phone.user_id = user_id
    phone.assigned_at = datetime.utcnow()
    phone.display_name = display_name
    db.session.commit()

    return jsonify({'success': True, 'phone_number': phone.to_dict()}), 201
