import logging
import json
import uuid
import time
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models.phone_number import PhoneNumber
from ..models.user_call_config import UserCallConfig
from ..models.call_log import CallLog
from ..models.call_analytics import CallAnalytics
from ..models.job import Job
from ..services.vapi_service import VapiService
from ..services.call_script_templates import get_template, list_templates as list_all_templates
from ..models.call_result import CallResult

logger = logging.getLogger(__name__)

calls_bp = Blueprint('calls', __name__)


# ─── Templates ─────────────────────────────────────────────────────────────


@calls_bp.route('/templates', methods=['GET'])
@jwt_required()
def get_templates():
    return jsonify({'templates': list_all_templates()}), 200


# ─── Call Routes ────────────────────────────────────────────────────────────


@calls_bp.route('/', methods=['POST'])
@jwt_required()
def initiate_call():
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    customer_number = data.get('customer_number')
    lead_context = data.get('lead_context')

    if not customer_number:
        return jsonify({'error': 'customer_number is required'}), 400

    # Get user's call config
    config = UserCallConfig.query.filter_by(user_id=user_id, is_active=True).first()
    if not config:
        return jsonify({'error': 'No active call configuration. Set up your config first.'}), 400

    # Check call window
    from ..services.language_service import is_in_call_window
    if not is_in_call_window(customer_number, config):
        return jsonify({'error': 'Outside allowed call window'}), 400

    # Get user's assigned phone number with Vapi import
    phone = PhoneNumber.query.filter_by(
        user_id=user_id,
        status=PhoneNumber.STATUS_ASSIGNED,
    ).filter(PhoneNumber.vapi_phone_id.isnot(None)).first()

    if not phone:
        return jsonify({'error': 'No assigned phone number with Vapi import. Contact admin.'}), 400

    shared_assistant_id = current_app.config.get('VAPI_SHARED_ASSISTANT_ID')
    if not shared_assistant_id:
        return jsonify({'error': 'Shared assistant not configured'}), 500

    # Build overrides from user config
    from ..services.call_override_builder import build_overrides
    overrides = build_overrides(config, customer_number, lead_context=lead_context)

    try:
        vapi = VapiService()
        vapi_result = vapi.create_call(
            assistant_id=shared_assistant_id,
            phone_number_id=phone.vapi_phone_id,
            customer_number=customer_number,
            overrides=overrides,
        )

        call_log = CallLog(
            user_id=user_id,
            vapi_call_id=vapi_result.get('id'),
            phone_number_id=phone.id,
            customer_number=customer_number,
            status=CallLog.STATUS_QUEUED,
            template_used=config.active_template,
            lead_context=json.dumps(lead_context) if lead_context else None,
        )
        db.session.add(call_log)
        db.session.commit()

        return jsonify({'success': True, 'call': call_log.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Initiate call error: {str(e)}")
        return jsonify({'error': str(e)}), 400


@calls_bp.route('/', methods=['GET'])
@jwt_required()
def list_calls():
    user_id = get_jwt_identity()
    status = request.args.get('status')
    direction = request.args.get('direction')
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 200)

    query = CallLog.query.filter_by(user_id=user_id)
    if status:
        query = query.filter_by(status=status)
    if direction:
        query = query.filter_by(direction=direction)
    query = query.order_by(CallLog.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'calls': [c.to_dict() for c in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
    }), 200


@calls_bp.route('/<int:call_id>', methods=['GET'])
@jwt_required()
def get_call(call_id):
    user_id = get_jwt_identity()
    call = CallLog.query.filter_by(id=call_id, user_id=user_id).first()
    if not call:
        return jsonify({'error': 'Call not found'}), 404
    return jsonify({'call': call.to_dict()}), 200


# ─── Call Analytics ────────────────────────────────────────────────────────


@calls_bp.route('/<int:call_id>/analytics', methods=['GET'])
@jwt_required()
def get_call_analytics(call_id):
    user_id = get_jwt_identity()
    call = CallLog.query.filter_by(id=call_id, user_id=user_id).first()
    if not call:
        return jsonify({'error': 'Call not found'}), 404
    analytics = CallAnalytics.query.filter_by(call_log_id=call_id).first()
    if not analytics:
        return jsonify({'error': 'No analytics yet'}), 404
    return jsonify({'analytics': analytics.to_dict()}), 200


# ─── Call Results ──────────────────────────────────────────────────────────


@calls_bp.route('/<int:call_id>/result', methods=['GET'])
@jwt_required()
def get_call_result(call_id):
    user_id = get_jwt_identity()
    result = CallResult.query.join(CallLog).filter(
        CallLog.id == call_id,
        CallLog.user_id == user_id,
    ).first()
    if not result:
        return jsonify({'error': 'No result found for this call'}), 404
    return jsonify({'result': result.to_dict()}), 200


@calls_bp.route('/results', methods=['GET'])
@jwt_required()
def list_call_results():
    user_id = get_jwt_identity()
    template = request.args.get('template')
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 200)

    query = CallResult.query.filter_by(user_id=user_id)
    if template:
        query = query.filter_by(template_name=template)
    if status:
        query = query.filter_by(extraction_status=status)
    query = query.order_by(CallResult.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        'results': [r.to_dict() for r in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
    }), 200


# ─── Batch Calling (Background Job) ────────────────────────────────────────


@calls_bp.route('/batch', methods=['POST'])
@jwt_required()
def batch_calls():
    user_id = get_jwt_identity()
    data = request.get_json() or {}

    customer_numbers = data.get('customer_numbers', [])
    delay_seconds = max(1, min(data.get('delay_seconds', 2), 10))

    if not customer_numbers or len(customer_numbers) > 50:
        return jsonify({'error': 'customer_numbers must be 1-50 numbers'}), 400

    # Validate config
    config = UserCallConfig.query.filter_by(user_id=user_id, is_active=True).first()
    if not config:
        return jsonify({'error': 'No active call configuration. Set up your config first.'}), 400

    # Validate phone
    phone = PhoneNumber.query.filter_by(
        user_id=user_id,
        status=PhoneNumber.STATUS_ASSIGNED,
    ).filter(PhoneNumber.vapi_phone_id.isnot(None)).first()
    if not phone:
        return jsonify({'error': 'No assigned phone number with Vapi import. Contact admin.'}), 400

    shared_assistant_id = current_app.config.get('VAPI_SHARED_ASSISTANT_ID')
    if not shared_assistant_id:
        return jsonify({'error': 'Shared assistant not configured'}), 500

    # Create a Job record
    job_id = str(uuid.uuid4())
    job = Job(
        id=job_id,
        user_id=user_id,
        job_type='batch_calls',
        status=Job.STATUS_PENDING,
        total_items=len(customer_numbers),
    )
    db.session.add(job)
    db.session.commit()

    # Schedule background job
    from ..extensions import scheduler
    scheduler.add_job(
        func=_execute_batch_calls,
        trigger='date',
        id=f'batch_calls_{job_id}',
        args=[current_app._get_current_object(), job_id, user_id, shared_assistant_id,
              phone.vapi_phone_id, phone.id, config.id, customer_numbers, delay_seconds],
        misfire_grace_time=300,
    )

    return jsonify({
        'success': True,
        'job_id': job_id,
        'message': 'Batch calling job queued',
        'total': len(customer_numbers),
    }), 202


@calls_bp.route('/batch/<string:job_id>', methods=['GET'])
@jwt_required()
def get_batch_status(job_id):
    user_id = get_jwt_identity()
    job = Job.query.filter_by(id=job_id, user_id=user_id).first()
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify({'success': True, 'job': job.to_dict()}), 200


def _execute_batch_calls(app, job_id, user_id, shared_assistant_id, vapi_phone_id,
                         phone_number_id, config_id, customer_numbers, delay_seconds):
    with app.app_context():
        job = Job.query.get(job_id)
        if not job:
            return
        job.mark_started()

        config = UserCallConfig.query.get(config_id)
        from ..services.call_override_builder import build_overrides

        success_count = 0
        error_count = 0

        for i, customer_number in enumerate(customer_numbers):
            try:
                overrides = build_overrides(config, customer_number) if config else None

                vapi = VapiService()
                vapi_result = vapi.create_call(
                    assistant_id=shared_assistant_id,
                    phone_number_id=vapi_phone_id,
                    customer_number=customer_number,
                    overrides=overrides,
                )

                call_log = CallLog(
                    user_id=user_id,
                    vapi_call_id=vapi_result.get('id'),
                    phone_number_id=phone_number_id,
                    customer_number=customer_number,
                    status=CallLog.STATUS_QUEUED,
                    template_used=config.active_template if config else None,
                )
                db.session.add(call_log)
                db.session.commit()
                success_count += 1

            except Exception as e:
                logger.error(f"Batch call {i+1}/{len(customer_numbers)} failed for {customer_number}: {str(e)}")
                error_count += 1

            job.update_progress(
                processed=i + 1,
                success=success_count,
                error=error_count,
            )

            # Delay between calls (skip after last)
            if i < len(customer_numbers) - 1:
                time.sleep(delay_seconds)

        job.mark_completed(result_data={
            'total': len(customer_numbers),
            'succeeded': success_count,
            'failed': error_count,
        })
