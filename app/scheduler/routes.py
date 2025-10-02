from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

scheduler_bp = Blueprint('scheduler', __name__)

@scheduler_bp.route('/jobs', methods=['GET'])
@jwt_required()
def get_jobs():
    """Get list of scheduled jobs"""
    try:
        from ..extensions import init_scheduler
        scheduler = init_scheduler()
        jobs = scheduler.get_jobs()
        return jsonify({
            'success': True,
            'jobs': jobs,
            'scheduler_running': scheduler.scheduler.running if scheduler.scheduler else False
        })
    except Exception as e:
        logging.error(f"Error getting jobs: {str(e)}")
        return jsonify({'error': 'Failed to get jobs'}), 500

@scheduler_bp.route('/jobs/<job_id>/trigger', methods=['POST'])
@jwt_required()
def trigger_job(job_id):
    """Manually trigger a job"""
    try:
        from ..extensions import init_scheduler
        scheduler = init_scheduler()
        success = scheduler.trigger_job(job_id)
        if success:
            return jsonify({'success': True, 'message': f'Job {job_id} triggered successfully'})
        else:
            return jsonify({'error': f'Failed to trigger job {job_id}'}), 400
    except Exception as e:
        logging.error(f"Error triggering job {job_id}: {str(e)}")
        return jsonify({'error': 'Failed to trigger job'}), 500

@scheduler_bp.route('/jobs/<job_id>/pause', methods=['POST'])
@jwt_required()
def pause_job(job_id):
    """Pause a job"""
    try:
        from ..extensions import init_scheduler
        scheduler = init_scheduler()
        success = scheduler.pause_job(job_id)
        if success:
            return jsonify({'success': True, 'message': f'Job {job_id} paused successfully'})
        else:
            return jsonify({'error': f'Failed to pause job {job_id}'}), 400
    except Exception as e:
        logging.error(f"Error pausing job {job_id}: {str(e)}")
        return jsonify({'error': 'Failed to pause job'}), 500

@scheduler_bp.route('/jobs/<job_id>/resume', methods=['POST'])
@jwt_required()
def resume_job(job_id):
    """Resume a job"""
    try:
        from ..extensions import init_scheduler
        scheduler = init_scheduler()
        success = scheduler.resume_job(job_id)
        if success:
            return jsonify({'success': True, 'message': f'Job {job_id} resumed successfully'})
        else:
            return jsonify({'error': f'Failed to resume job {job_id}'}), 400
    except Exception as e:
        logging.error(f"Error resuming job {job_id}: {str(e)}")
        return jsonify({'error': 'Failed to resume job'}), 500
