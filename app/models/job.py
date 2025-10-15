from datetime import datetime
from ..extensions import db
import json

class Job(db.Model):
    """Model for tracking background jobs"""
    __tablename__ = 'jobs'
    
    # Status constants
    STATUS_PENDING = 'pending'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    STATUS_CANCELLED = 'cancelled'
    
    # Job type constants
    TYPE_SYNC_POSTS = 'sync_posts'
    TYPE_SYNC_COMMENTS = 'sync_comments'
    TYPE_SYNC_ALL = 'sync_all'
    
    id = db.Column(db.String(50), primary_key=True)  # UUID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_type = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default=STATUS_PENDING, nullable=False)
    
    # Job metadata
    total_items = db.Column(db.Integer, default=0)
    processed_items = db.Column(db.Integer, default=0)
    success_count = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    
    # Results and error information
    result = db.Column(db.Text, nullable=True)  # JSON string
    error_message = db.Column(db.Text, nullable=True)
    error_details = db.Column(db.Text, nullable=True)  # JSON string for detailed errors
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='jobs')
    
    def to_dict(self):
        """Convert job to dictionary"""
        result_data = None
        if self.result:
            try:
                result_data = json.loads(self.result)
            except:
                result_data = self.result
        
        error_details_data = None
        if self.error_details:
            try:
                error_details_data = json.loads(self.error_details)
            except:
                error_details_data = self.error_details
        
        # Calculate progress percentage
        progress = 0
        if self.total_items > 0:
            progress = int((self.processed_items / self.total_items) * 100)
        elif self.status == self.STATUS_COMPLETED:
            progress = 100
        
        # Calculate duration
        duration = None
        if self.started_at and self.completed_at:
            duration = (self.completed_at - self.started_at).total_seconds()
        elif self.started_at:
            duration = (datetime.utcnow() - self.started_at).total_seconds()
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'job_type': self.job_type,
            'status': self.status,
            'progress': progress,
            'total_items': self.total_items,
            'processed_items': self.processed_items,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'result': result_data,
            'error_message': self.error_message,
            'error_details': error_details_data,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'duration_seconds': duration
        }
    
    def update_progress(self, processed=None, success=None, error=None, total=None):
        """Update job progress"""
        if processed is not None:
            self.processed_items = processed
        if success is not None:
            self.success_count = success
        if error is not None:
            self.error_count = error
        if total is not None:
            self.total_items = total
        self.last_updated = datetime.utcnow()
        db.session.commit()
    
    def mark_started(self):
        """Mark job as started"""
        self.status = self.STATUS_IN_PROGRESS
        self.started_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()
        db.session.commit()
    
    def mark_completed(self, result_data=None):
        """Mark job as completed"""
        self.status = self.STATUS_COMPLETED
        self.completed_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()
        if result_data:
            self.result = json.dumps(result_data) if isinstance(result_data, dict) else str(result_data)
        db.session.commit()
    
    def mark_failed(self, error_message, error_details=None):
        """Mark job as failed"""
        self.status = self.STATUS_FAILED
        self.completed_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()
        self.error_message = error_message
        if error_details:
            self.error_details = json.dumps(error_details) if isinstance(error_details, dict) else str(error_details)
        db.session.commit()
    
    def mark_cancelled(self):
        """Mark job as cancelled"""
        self.status = self.STATUS_CANCELLED
        self.completed_at = datetime.utcnow()
        self.last_updated = datetime.utcnow()
        db.session.commit()

