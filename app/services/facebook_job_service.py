"""
Facebook Job Service
Handles background jobs for Facebook data synchronization
"""
import logging
import uuid
import time
from datetime import datetime
from ..models import Job, User, FacebookPost
from ..extensions import db
from .facebook_service import FacebookService

logger = logging.getLogger(__name__)


class FacebookJobService:
    """Service for managing Facebook synchronization background jobs"""
    
    @staticmethod
    def create_job(user_id, job_type):
        """Create a new background job"""
        try:
            job_id = str(uuid.uuid4())
            job = Job(
                id=job_id,
                user_id=user_id,
                job_type=job_type,
                status=Job.STATUS_PENDING
            )
            db.session.add(job)
            db.session.commit()
            
            logger.info(f"Created job {job_id} for user {user_id}, type: {job_type}")
            return job
        except Exception as e:
            logger.error(f"Error creating job: {str(e)}")
            db.session.rollback()
            return None
    
    @staticmethod
    def get_job(job_id):
        """Get job by ID"""
        return Job.query.get(job_id)
    
    @staticmethod
    def get_user_jobs(user_id, limit=20, status=None):
        """Get all jobs for a user"""
        query = Job.query.filter_by(user_id=user_id)
        if status:
            query = query.filter_by(status=status)
        jobs = query.order_by(Job.created_at.desc()).limit(limit).all()
        return jobs
    
    @staticmethod
    def execute_sync_posts_job(job_id):
        """
        Execute a post synchronization job
        This runs in the background
        """
        from flask import current_app
        
        with current_app.app_context():
            try:
                job = Job.query.get(job_id)
                if not job:
                    logger.error(f"Job {job_id} not found")
                    return
                
                # Mark job as started
                job.mark_started()
                logger.info(f"Starting post sync job {job_id} for user {job.user_id}")
                
                # Get user
                user = User.query.get(job.user_id)
                if not user:
                    job.mark_failed("User not found")
                    return
                
                if not user.facebook_access_token:
                    job.mark_failed("No Facebook access token found")
                    return
                
                # Check token expiration
                if user.facebook_token_expires and user.facebook_token_expires < datetime.utcnow():
                    job.mark_failed("Facebook access token expired")
                    return
                
                # Fetch posts with pagination
                total_posts = 0
                success_count = 0
                error_count = 0
                all_posts = []
                
                # Facebook allows max 100 posts per request
                limit_per_request = 100
                max_requests = 5  # Max 5 requests to avoid rate limits (500 posts max)
                
                next_url = None
                for request_num in range(max_requests):
                    try:
                        if next_url:
                            # Use pagination URL
                            result = FacebookService._fetch_posts_from_url(next_url)
                        else:
                            # First request
                            result = FacebookService.fetch_user_posts(
                                user.id, 
                                limit=limit_per_request
                            )
                        
                        if 'error' in result:
                            logger.error(f"Error fetching posts: {result['error']}")
                            error_count += 1
                            break
                        
                        posts = result.get('posts', [])
                        if not posts:
                            logger.info("No more posts to fetch")
                            break
                        
                        total_posts += len(posts)
                        success_count += len(posts)
                        all_posts.extend(posts)
                        
                        # Update job progress
                        job.update_progress(
                            processed=total_posts,
                            success=success_count,
                            error=error_count,
                            total=total_posts
                        )
                        
                        logger.info(f"Fetched {len(posts)} posts, total: {total_posts}")
                        
                        # Check if there's a next page
                        next_url = result.get('next_url')
                        if not next_url:
                            break
                        
                        # Small delay to respect rate limits
                        time.sleep(1)
                        
                    except Exception as e:
                        logger.error(f"Error in request {request_num}: {str(e)}")
                        error_count += 1
                        break
                
                # Mark job as completed
                result_data = {
                    'total_posts': total_posts,
                    'success_count': success_count,
                    'error_count': error_count,
                    'message': f'Successfully synchronized {success_count} posts'
                }
                
                job.update_progress(
                    processed=total_posts,
                    success=success_count,
                    error=error_count,
                    total=total_posts
                )
                job.mark_completed(result_data)
                
                logger.info(f"Completed post sync job {job_id}: {result_data}")
                
            except Exception as e:
                logger.error(f"Error executing post sync job {job_id}: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                
                job = Job.query.get(job_id)
                if job:
                    job.mark_failed(str(e), {'traceback': traceback.format_exc()})
    
    @staticmethod
    def execute_sync_comments_job(job_id):
        """
        Execute a comment synchronization job
        This runs in the background
        """
        from flask import current_app
        
        with current_app.app_context():
            try:
                job = Job.query.get(job_id)
                if not job:
                    logger.error(f"Job {job_id} not found")
                    return
                
                # Mark job as started
                job.mark_started()
                logger.info(f"Starting comment sync job {job_id} for user {job.user_id}")
                
                # Get user
                user = User.query.get(job.user_id)
                if not user:
                    job.mark_failed("User not found")
                    return
                
                if not user.facebook_access_token:
                    job.mark_failed("No Facebook access token found")
                    return
                
                # Check token expiration
                if user.facebook_token_expires and user.facebook_token_expires < datetime.utcnow():
                    job.mark_failed("Facebook access token expired")
                    return
                
                # Get all user's posts from database
                posts = FacebookPost.query.filter_by(user_id=user.id).all()
                
                if not posts:
                    job.mark_completed({
                        'message': 'No posts found to fetch comments for',
                        'total_posts': 0,
                        'total_comments': 0
                    })
                    return
                
                total_posts = len(posts)
                processed_posts = 0
                total_comments = 0
                success_count = 0
                error_count = 0
                errors = []
                
                # Update total items
                job.update_progress(total=total_posts, processed=0)
                
                # Fetch comments for each post
                for post in posts:
                    try:
                        logger.info(f"Fetching comments for post {post.id}")
                        
                        result = FacebookService.fetch_post_comments(
                            post.id,
                            user.facebook_access_token,
                            limit=100  # Fetch up to 100 comments per post
                        )
                        
                        if 'error' in result:
                            logger.error(f"Error fetching comments for post {post.id}: {result['error']}")
                            error_count += 1
                            errors.append({
                                'post_id': post.id,
                                'error': result['error']
                            })
                        else:
                            comments_fetched = result.get('comments_count', 0)
                            total_comments += comments_fetched
                            success_count += 1
                            logger.info(f"Fetched {comments_fetched} comments for post {post.id}")
                        
                        processed_posts += 1
                        
                        # Update job progress
                        job.update_progress(
                            processed=processed_posts,
                            success=success_count,
                            error=error_count
                        )
                        
                        # Small delay to respect rate limits
                        time.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"Error processing post {post.id}: {str(e)}")
                        error_count += 1
                        errors.append({
                            'post_id': post.id,
                            'error': str(e)
                        })
                        processed_posts += 1
                        job.update_progress(
                            processed=processed_posts,
                            error=error_count
                        )
                
                # Mark job as completed
                result_data = {
                    'total_posts': total_posts,
                    'processed_posts': processed_posts,
                    'total_comments': total_comments,
                    'success_count': success_count,
                    'error_count': error_count,
                    'message': f'Successfully synchronized comments for {success_count} posts, total {total_comments} comments',
                    'errors': errors if errors else None
                }
                
                job.mark_completed(result_data)
                
                logger.info(f"Completed comment sync job {job_id}: {result_data}")
                
            except Exception as e:
                logger.error(f"Error executing comment sync job {job_id}: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                
                job = Job.query.get(job_id)
                if job:
                    job.mark_failed(str(e), {'traceback': traceback.format_exc()})
    
    @staticmethod
    def execute_sync_all_job(job_id):
        """
        Execute a full synchronization job (posts + comments)
        This runs in the background
        """
        from flask import current_app
        
        with current_app.app_context():
            try:
                job = Job.query.get(job_id)
                if not job:
                    logger.error(f"Job {job_id} not found")
                    return
                
                # Mark job as started
                job.mark_started()
                logger.info(f"Starting full sync job {job_id} for user {job.user_id}")
                
                # First, sync posts
                logger.info("Step 1: Syncing posts...")
                posts_job_id = str(uuid.uuid4())
                posts_job = Job(
                    id=posts_job_id,
                    user_id=job.user_id,
                    job_type=Job.TYPE_SYNC_POSTS,
                    status=Job.STATUS_PENDING
                )
                db.session.add(posts_job)
                db.session.commit()
                
                FacebookJobService.execute_sync_posts_job(posts_job_id)
                
                # Check if posts sync succeeded
                posts_job = Job.query.get(posts_job_id)
                if posts_job.status != Job.STATUS_COMPLETED:
                    job.mark_failed(f"Posts synchronization failed: {posts_job.error_message}")
                    return
                
                # Then, sync comments
                logger.info("Step 2: Syncing comments...")
                comments_job_id = str(uuid.uuid4())
                comments_job = Job(
                    id=comments_job_id,
                    user_id=job.user_id,
                    job_type=Job.TYPE_SYNC_COMMENTS,
                    status=Job.STATUS_PENDING
                )
                db.session.add(comments_job)
                db.session.commit()
                
                FacebookJobService.execute_sync_comments_job(comments_job_id)
                
                # Check if comments sync succeeded
                comments_job = Job.query.get(comments_job_id)
                
                # Mark main job as completed
                result_data = {
                    'posts_job_id': posts_job_id,
                    'comments_job_id': comments_job_id,
                    'posts_result': posts_job.to_dict(),
                    'comments_result': comments_job.to_dict(),
                    'message': 'Full synchronization completed'
                }
                
                job.mark_completed(result_data)
                
                logger.info(f"Completed full sync job {job_id}")
                
            except Exception as e:
                logger.error(f"Error executing full sync job {job_id}: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                
                job = Job.query.get(job_id)
                if job:
                    job.mark_failed(str(e), {'traceback': traceback.format_exc()})

