import logging
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.phone_number import PhoneNumber
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

    # only 1 number per user
    existing = PhoneNumber.get_by_user(user_id)
    if existing:
        return jsonify({'error': 'Only 1 number per user'}), 400

    vapi_tag = f"user_{user_id}"
    if display_name:
        vapi_tag = f"user_{user_id}_{display_name}"
    result = PhonePoolService.buy_and_add_to_pool(phone_number, country_code, vapi_name=vapi_tag)
    if 'error' in result:
        return jsonify({'error': result['error']}), 400

    # assign to user
    phone = PhoneNumber.query.filter_by(phone_number=phone_number).first()
    phone.status = PhoneNumber.STATUS_ASSIGNED
    phone.user_id = user_id
    phone.assigned_at = datetime.utcnow()
    phone.display_name = display_name
    db.session.commit()

    return jsonify({'success': True, 'phone_number': phone.to_dict()}), 201


@phone_bp.route('/my-number', methods=['GET'])
@jwt_required()
def my_number():
    user_id = get_jwt_identity()
    numbers = PhoneNumber.get_by_user(user_id)
    phone = numbers[0] if numbers else None
    return jsonify({'phone_number': phone.to_dict() if phone else None}), 200


@phone_bp.route('/my-number', methods=['PUT'])
@jwt_required()
def update_my_number():
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    numbers = PhoneNumber.get_by_user(user_id)
    if not numbers:
        return jsonify({'error': 'No number assigned'}), 404

    phone = numbers[0]
    if 'display_name' in data:
        phone.display_name = data['display_name']
        db.session.commit()

    return jsonify({'success': True, 'phone_number': phone.to_dict()}), 200
