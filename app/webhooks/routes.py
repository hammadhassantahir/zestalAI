import logging
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from ..extensions import db
from ..models.call_log import CallLog
from ..models.call_result import CallResult
from ..models.vapi_assistant import VapiAssistant

logger = logging.getLogger(__name__)

webhooks_bp = Blueprint('webhooks', __name__)


@webhooks_bp.route('/vapi', methods=['POST'])
def vapi_webhook():
    try:
        # Validate webhook secret
        webhook_secret = current_app.config.get('VAPI_WEBHOOK_SECRET')
        if webhook_secret:
            received_secret = request.headers.get('x-vapi-secret', '')
            if received_secret != webhook_secret:
                logger.warning(f"Vapi webhook auth failed from {request.remote_addr}")
                return jsonify({'error': 'Unauthorized'}), 401
        else:
            logger.warning("VAPI_WEBHOOK_SECRET not configured — webhook auth disabled")

        data = request.get_json()
        if not data:
            return jsonify({'success': True}), 200

        message = data.get('message', {})
        msg_type = message.get('type', '')
        call_data = message.get('call', {})
        vapi_call_id = call_data.get('id')

        logger.info(f"Vapi webhook received: type={msg_type}, call_id={vapi_call_id}")

        if msg_type == 'status-update':
            _handle_status_update(vapi_call_id, message)
        elif msg_type == 'end-of-call-report':
            _handle_end_of_call_report(vapi_call_id, message)
        elif msg_type == 'function-call':
            result = _handle_function_call(vapi_call_id, message)
            return jsonify({'result': json.dumps(result)}), 200
        elif msg_type == 'hang':
            _handle_hang(vapi_call_id, message)

        return jsonify({'success': True}), 200

    except Exception as e:
        logger.error(f"Vapi webhook error: {str(e)}")
        return jsonify({'success': False}), 200  # Still 200 to prevent retries


def _handle_status_update(vapi_call_id, message):
    if not vapi_call_id:
        return

    call = CallLog.query.filter_by(vapi_call_id=vapi_call_id).first()
    if not call:
        logger.warning(f"CallLog not found for vapi_call_id: {vapi_call_id}")
        return

    new_status = message.get('status', '')
    call.status = new_status

    if new_status == 'in-progress':
        call.started_at = datetime.utcnow()

    db.session.commit()
    logger.info(f"Call {vapi_call_id} status updated to: {new_status}")


def _handle_end_of_call_report(vapi_call_id, message):
    if not vapi_call_id:
        return

    call = CallLog.query.filter_by(vapi_call_id=vapi_call_id).first()
    if not call:
        logger.warning(f"CallLog not found for vapi_call_id: {vapi_call_id}")
        return

    call.status = CallLog.STATUS_ENDED
    call.end_reason = message.get('endedReason')
    call.duration_seconds = message.get('durationSeconds')
    call.transcript = message.get('transcript')
    call.summary = message.get('summary')
    call.recording_url = message.get('recordingUrl')
    call.cost = message.get('cost')

    # Parse endedAt
    ended_at_str = message.get('endedAt')
    if ended_at_str:
        try:
            call.ended_at = datetime.fromisoformat(ended_at_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            call.ended_at = datetime.utcnow()
    else:
        call.ended_at = datetime.utcnow()

    # Store analysis as structured data
    analysis = message.get('analysis')
    if analysis:
        call.structured_data = json.dumps(analysis)

    db.session.commit()
    logger.info(f"Call {vapi_call_id} end-of-call report processed (duration: {call.duration_seconds}s)")

    # Create CallResult if this call used a template-based assistant (backward compat)
    template_name = None
    if call.template_used:
        template_name = call.template_used
    elif call.assistant_id:
        assistant = VapiAssistant.query.get(call.assistant_id)
        if assistant and assistant.template_name:
            template_name = assistant.template_name

    if template_name:
        structured = message.get('analysis', {}).get('structuredData')
        call_result = CallResult(
            call_log_id=call.id,
            user_id=call.user_id,
            template_name=template_name,
            extracted_data=json.dumps(structured) if structured else None,
            extraction_status=CallResult.STATUS_COMPLETED if structured else CallResult.STATUS_FAILED,
        )
        db.session.add(call_result)
        db.session.commit()
        logger.info(f"CallResult created for call {vapi_call_id} (template: {template_name})")

    # trigger async LLM analysis
    try:
        from ..extensions import scheduler
        from flask import current_app
        scheduler.add_job(
            func=_run_call_analysis,
            trigger='date',
            id=f'analyze_call_{call.id}',
            args=[current_app._get_current_object(), call.id],
            misfire_grace_time=300,
        )
    except Exception as e:
        logger.warning(f"Failed to schedule analysis for {vapi_call_id}: {str(e)}")


def _handle_function_call(vapi_call_id, message):
    func_call = message.get('functionCall', {})
    func_name = func_call.get('name', '')
    func_params = func_call.get('parameters', {})

    logger.info(f"Call {vapi_call_id} function call: {func_name}")

    # Route by function name
    if func_name == 'bookAppointment':
        return {'result': 'Appointment booked'}
    elif func_name == 'lookupCustomer':
        return {'result': 'Customer found'}
    else:
        logger.warning(f"Unknown function: {func_name}")
        return {'result': 'Function not implemented'}


def _handle_hang(vapi_call_id, message):
    if not vapi_call_id:
        return

    call = CallLog.query.filter_by(vapi_call_id=vapi_call_id).first()
    if not call:
        logger.warning(f"CallLog not found for vapi_call_id: {vapi_call_id}")
        return

    call.status = 'hang'
    db.session.commit()
    logger.info(f"Call {vapi_call_id} hang event received")


def _run_call_analysis(app, call_log_id):
    with app.app_context():
        from ..services.call_analytics_service import analyze_call
        analyze_call(call_log_id)
