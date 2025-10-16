#!/usr/bin/env python3
"""
Scheduler Service for Facebook Background Tasks
Handles scheduled execution of Facebook data fetching and cleanup
"""

import logging
import atexit
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from flask import current_app

from .facebook_service import FacebookService
from ..models import User
from ..extensions import db

class SchedulerService:
    """Service for managing scheduled tasks"""
    
    def __init__(self, app=None):
        self.scheduler = None
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the scheduler with Flask app context"""
        self.app = app
        
        # Configure scheduler with memory job store (simpler setup)
        self.scheduler = BackgroundScheduler(timezone='UTC')
        
        # Add event listeners for logging
        self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)
        
        # Register shutdown handler
        atexit.register(lambda: self.shutdown())
        
        logging.info("Scheduler service initialized")
    
    def start(self):
        """Start the scheduler"""
        if self.scheduler and not self.scheduler.running:
            self.scheduler.start()
            logging.info("Scheduler started")
            
            # Add default jobs
            self.add_facebook_jobs()
    
    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logging.info("Scheduler shutdown")
    
    def add_facebook_jobs(self):
        """Add Facebook-related scheduled jobs"""
        
        # Job 1: Fetch Facebook posts every hour
        self.scheduler.add_job(
            func=self._fetch_all_user_posts,
            # trigger=IntervalTrigger(hours=5), 
            trigger=IntervalTrigger(minutes=59),
            id='fetch_facebook_posts',
            name='Fetch Facebook Posts',
            replace_existing=True,
            max_instances=1  # Prevent overlapping executions
        )
        
        # Job 2: Clean up expired tokens daily at 2 AM
        self.scheduler.add_job(
            func=self._cleanup_expired_tokens,
            trigger=CronTrigger(hour=2, minute=0),
            id='cleanup_expired_tokens',
            name='Cleanup Expired Tokens',
            replace_existing=True,
            max_instances=1
        )
        
        # Job 3: Health check every 30 minutes
        self.scheduler.add_job(
            func=self._health_check,
            trigger=IntervalTrigger(minutes=30),
            id='scheduler_health_check',
            name='Scheduler Health Check',
            replace_existing=True
        )
        
        logging.info("Facebook scheduler jobs added")
    
    def _fetch_all_user_posts(self):
        """Fetch posts for all users with valid Facebook tokens"""
        with self.app.app_context():
            try:
                logging.info("*****************************Starting scheduled Facebook posts fetch")
                
                # Get all users with Facebook access tokens that haven't expired
                users = User.query.filter(
                    User.facebook_access_token.isnot(None),
                    User.facebook_token_expires > datetime.utcnow()
                ).all()
                
                logging.info(f"Found {len(users)} users with valid Facebook tokens")
                
                total_posts = 0
                for user in users:
                    try:
                        logging.info(f"Fetching posts for user {user.id} ({user.email})")
                        
                        # Fetch posts with a reasonable limit
                        result = FacebookService.fetch_user_posts(user.id, limit=25)
                        
                        if 'error' in result:
                            logging.error(f"Error fetching posts for user {user.id}: {result['error']}")
                            continue
                        
                        posts_count = result.get('posts_count', 0)
                        total_posts += posts_count
                        logging.info(f"Successfully fetched {posts_count} posts for user {user.id}")
                        
                    except Exception as e:
                        logging.error(f"Error processing user {user.id}: {str(e)}")
                        continue
                
                logging.info(f"Scheduled Facebook posts fetch completed. Total posts fetched: {total_posts}")
                
            except Exception as e:
                logging.error(f"Error in scheduled fetch_all_user_posts: {str(e)}")
    
    def _cleanup_expired_tokens(self):
        """Clean up expired Facebook tokens"""
        with self.app.app_context():
            try:
                logging.info("Starting scheduled token cleanup")
                
                expired_users = User.query.filter(
                    User.facebook_access_token.isnot(None),
                    User.facebook_token_expires < datetime.utcnow()
                ).all()
                
                logging.info(f"Found {len(expired_users)} users with expired tokens")
                
                for user in expired_users:
                    logging.info(f"Clearing expired token for user {user.id} ({user.email})")
                    user.facebook_access_token = None
                    user.facebook_token_expires = None
                
                db.session.commit()
                logging.info("Scheduled token cleanup completed")
                
            except Exception as e:
                logging.error(f"Error in scheduled cleanup_expired_tokens: {str(e)}")
                db.session.rollback()
    
    def _health_check(self):
        """Health check for scheduler"""
        logging.info(f"Scheduler health check - Running: {self.scheduler.running if self.scheduler else False}")
    
    def _job_executed(self, event):
        """Handle successful job execution"""
        logging.info(f"Job {event.job_id} executed successfully at {event.scheduled_run_time}")
    
    def _job_error(self, event):
        """Handle job execution errors"""
        logging.error(f"Job {event.job_id} failed with exception: {event.exception}")
    
    def get_jobs(self):
        """Get list of scheduled jobs"""
        if self.scheduler:
            return [
                {
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                }
                for job in self.scheduler.get_jobs()
            ]
        return []
    
    def trigger_job(self, job_id):
        """Manually trigger a job"""
        if self.scheduler:
            try:
                self.scheduler.modify_job(job_id, next_run_time=datetime.utcnow())
                logging.info(f"Job {job_id} triggered manually")
                return True
            except Exception as e:
                logging.error(f"Error triggering job {job_id}: {str(e)}")
                return False
        return False
    
    def pause_job(self, job_id):
        """Pause a job"""
        if self.scheduler:
            try:
                self.scheduler.pause_job(job_id)
                logging.info(f"Job {job_id} paused")
                return True
            except Exception as e:
                logging.error(f"Error pausing job {job_id}: {str(e)}")
                return False
        return False
    
    def resume_job(self, job_id):
        """Resume a job"""
        if self.scheduler:
            try:
                self.scheduler.resume_job(job_id)
                logging.info(f"Job {job_id} resumed")
                return True
            except Exception as e:
                logging.error(f"Error resuming job {job_id}: {str(e)}")
                return False
        return False
    
    def run_job_async(self, func, *args, **kwargs):
        """
        Run a job asynchronously in the background
        This adds a one-time job that runs immediately
        """
        if self.scheduler:
            try:
                job = self.scheduler.add_job(
                    func=func,
                    args=args,
                    kwargs=kwargs,
                    trigger='date',  # Run once
                    run_date=datetime.utcnow(),
                    misfire_grace_time=None,
                    coalesce=False,
                    max_instances=1
                )
                logging.info(f"Background job scheduled: {job.id}")
                return job.id
            except Exception as e:
                logging.error(f"Error scheduling background job: {str(e)}")
                return None
        return None

# Global scheduler instance
scheduler_service = SchedulerService()
