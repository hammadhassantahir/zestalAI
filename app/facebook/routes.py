"""
Facebook Sync Routes
Endpoints for manual synchronization of Facebook posts and comments
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

from ..models import Job, User
from ..services.facebook_job_service import FacebookJobService
from ..services.scheduler_service import scheduler_service

logger = logging.getLogger(__name__)

facebook_bp = Blueprint('facebook', __name__)


@facebook_bp.route('/sync/posts', methods=['POST'])
@jwt_required()
def sync_posts():
    """
    Manually trigger Facebook post synchronization
    This creates a background job and returns the job ID
    
    Returns:
        200: Job created successfully with job_id
        400: Error creating job
        401: Unauthorized
    """
    try:
        current_user_id = get_jwt_identity()
        
        logger.info(f"Manual post sync requested by user {current_user_id}")
        
        # Verify user has Facebook access token
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.facebook_access_token:
            return jsonify({
                'error': 'No Facebook access token found',
                'message': 'Please authenticate with Facebook first'
            }), 400
        
        # Create job
        job = FacebookJobService.create_job(current_user_id, Job.TYPE_SYNC_POSTS)
        
        if not job:
            return jsonify({'error': 'Failed to create job'}), 500
        
        # Schedule job to run in background
        scheduler_service.run_job_async(
            FacebookJobService.execute_sync_posts_job,
            job.id
        )
        
        logger.info(f"Post sync job {job.id} created and scheduled for user {current_user_id}")
        
        return jsonify({
            'success': True,
            'job_id': job.id,
            'message': 'Post synchronization job started',
            'job': job.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in sync_posts endpoint: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Internal server error'}), 500


@facebook_bp.route('/sync/comments', methods=['POST'])
@jwt_required()
def sync_comments():
    """
    Manually trigger comment synchronization for all user's posts
    This creates a background job and returns the job ID
    
    Returns:
        200: Job created successfully with job_id
        400: Error creating job
        401: Unauthorized
    """
    try:
        current_user_id = get_jwt_identity()
        
        logger.info(f"Manual comment sync requested by user {current_user_id}")
        
        # Verify user has Facebook access token
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.facebook_access_token:
            return jsonify({
                'error': 'No Facebook access token found',
                'message': 'Please authenticate with Facebook first'
            }), 400
        
        # Create job
        job = FacebookJobService.create_job(current_user_id, Job.TYPE_SYNC_COMMENTS)
        
        if not job:
            return jsonify({'error': 'Failed to create job'}), 500
        
        # Schedule job to run in background
        scheduler_service.run_job_async(
            FacebookJobService.execute_sync_comments_job,
            job.id
        )
        
        logger.info(f"Comment sync job {job.id} created and scheduled for user {current_user_id}")
        
        return jsonify({
            'success': True,
            'job_id': job.id,
            'message': 'Comment synchronization job started',
            'job': job.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in sync_comments endpoint: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Internal server error'}), 500


@facebook_bp.route('/sync/all', methods=['POST'])
@jwt_required()
def sync_all():
    """
    Manually trigger full synchronization (posts + comments)
    This creates a background job and returns the job ID
    
    Returns:
        200: Job created successfully with job_id
        400: Error creating job
        401: Unauthorized
    """
    try:
        current_user_id = get_jwt_identity()
        
        logger.info(f"Manual full sync requested by user {current_user_id}")
        
        # Verify user has Facebook access token
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if not user.facebook_access_token:
            return jsonify({
                'error': 'No Facebook access token found',
                'message': 'Please authenticate with Facebook first'
            }), 400
        
        # Create job
        job = FacebookJobService.create_job(current_user_id, Job.TYPE_SYNC_ALL)
        
        if not job:
            return jsonify({'error': 'Failed to create job'}), 500
        
        # Schedule job to run in background
        scheduler_service.run_job_async(
            FacebookJobService.execute_sync_all_job,
            job.id
        )
        
        logger.info(f"Full sync job {job.id} created and scheduled for user {current_user_id}")
        
        return jsonify({
            'success': True,
            'job_id': job.id,
            'message': 'Full synchronization job started',
            'job': job.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in sync_all endpoint: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Internal server error'}), 500


@facebook_bp.route('/jobs/<job_id>', methods=['GET'])
@jwt_required()
def get_job_status(job_id):
    """
    Get the status of a background job
    
    Args:
        job_id: The ID of the job to check
    
    Returns:
        200: Job status and details
        403: Job doesn't belong to user
        404: Job not found
    """
    try:
        current_user_id = get_jwt_identity()
        
        job = FacebookJobService.get_job(job_id)
        
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        # Verify job belongs to current user
        if str(job.user_id) != str(current_user_id):
            return jsonify({'error': 'Unauthorized'}), 403
        
        return jsonify({
            'success': True,
            'job': job.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_job_status endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@facebook_bp.route('/jobs', methods=['GET'])
@jwt_required()
def get_user_jobs():
    """
    Get all jobs for the current user
    
    Query params:
        limit: Number of jobs to return (default: 20)
        status: Filter by job status (optional)
    
    Returns:
        200: List of jobs
    """
    try:
        current_user_id = get_jwt_identity()
        
        limit = request.args.get('limit', 20, type=int)
        status = request.args.get('status', None)
        
        jobs = FacebookJobService.get_user_jobs(current_user_id, limit, status)
        
        return jsonify({
            'success': True,
            'jobs': [job.to_dict() for job in jobs],
            'count': len(jobs)
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_user_jobs endpoint: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@facebook_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_facebook_stats():
    """
    Get Facebook synchronization statistics for the current user
    
    Returns:
        200: Statistics including post count, comment count, last sync, etc.
    """
    try:
        current_user_id = get_jwt_identity()
        
        from ..models import FacebookPost, FacebookComment
        
        user = User.query.get(current_user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get post statistics
        total_posts = FacebookPost.query.filter_by(user_id=current_user_id).count()
        
        # Get comment statistics
        post_ids = [post.id for post in FacebookPost.query.filter_by(user_id=current_user_id).all()]
        total_comments = FacebookComment.query.filter(FacebookComment.post_id.in_(post_ids)).count() if post_ids else 0
        
        # Get last sync info
        last_sync_job = Job.query.filter_by(
            user_id=current_user_id,
            status=Job.STATUS_COMPLETED
        ).order_by(Job.completed_at.desc()).first()
        
        # Get pending/in-progress jobs
        active_jobs = Job.query.filter_by(user_id=current_user_id).filter(
            Job.status.in_([Job.STATUS_PENDING, Job.STATUS_IN_PROGRESS])
        ).count()
        
        # Token status
        token_valid = False
        token_expires = None
        if user.facebook_access_token and user.facebook_token_expires:
            from datetime import datetime
            token_valid = user.facebook_token_expires > datetime.utcnow()
            token_expires = user.facebook_token_expires.isoformat()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_posts': total_posts,
                'total_comments': total_comments,
                'active_jobs': active_jobs,
                'last_sync': last_sync_job.to_dict() if last_sync_job else None,
                'token_status': {
                    'valid': token_valid,
                    'expires_at': token_expires
                }
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_facebook_stats endpoint: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': 'Internal server error'}), 500

