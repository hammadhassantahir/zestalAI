from datetime import datetime
from ..extensions import db

class FacebookPost(db.Model):
    __tablename__ = 'facebook_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    facebook_post_id = db.Column(db.String(255), unique=True, nullable=False)
    message = db.Column(db.Text, nullable=True)
    story = db.Column(db.Text, nullable=True)  # For posts without message (like photo uploads)
    post_type = db.Column(db.String(50), nullable=True)  # status, photo, video, link, etc.
    permalink_url = db.Column(db.Text, nullable=True)
    created_time = db.Column(db.DateTime, nullable=True)  # When the post was created on Facebook
    updated_time = db.Column(db.DateTime, nullable=True)  # When the post was last updated on Facebook
    likes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    shares_count = db.Column(db.Integer, default=0)
    privacy_visibility = db.Column(db.String(50), nullable=True)  # public, friends, limited, custom
    
    # Metadata
    fetched_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='facebook_posts')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'facebook_post_id': self.facebook_post_id,
            'message': self.message,
            'story': self.story,
            'post_type': self.post_type,
            'permalink_url': self.permalink_url,
            'created_time': self.created_time.isoformat() if self.created_time else None,
            'updated_time': self.updated_time.isoformat() if self.updated_time else None,
            'likes_count': self.likes_count,
            'comments_count': self.comments_count,
            'shares_count': self.shares_count,
            'privacy_visibility': self.privacy_visibility,
            'fetched_at': self.fetched_at.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }

class FacebookComment(db.Model):
    __tablename__ = 'facebook_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('facebook_posts.id'), nullable=False)
    facebook_comment_id = db.Column(db.String(255), unique=True, nullable=False)
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('facebook_comments.id'), nullable=True)  # For replies/sub-comments
    message = db.Column(db.Text, nullable=True)
    from_id = db.Column(db.String(100), nullable=True)  # ID of the person who commented
    from_name = db.Column(db.String(255), nullable=True)  # Name of the person who commented
    likes_count = db.Column(db.Integer, default=0)
    comment_date = db.Column(db.String(255), nullable=True)
    post_url = db.Column(db.String(255), nullable=True)
    has_liked = db.Column(db.Boolean, default=False)
    language = db.Column(db.String(255), nullable=True)
    self_comment = db.Column(db.Boolean, default=False)
    fetched_at = db.Column(db.DateTime, default=datetime.utcnow)
    ai_reply = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    # Relationships
    post = db.relationship('FacebookPost', backref='comments')
    parent = db.relationship('FacebookComment', remote_side=[id], backref='replies')
    user = db.relationship('User', backref='facebook_comments')
    
    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'facebook_comment_id': self.facebook_comment_id,
            'message': self.message,
            'from_id': self.from_id,
            'from_name': self.from_name,
            'comment_date': self.comment_date,
            'likes_count': self.likes_count,
            'parent_comment_id': self.parent_comment_id,
            'post_url': self.post_url,
            'has_liked': self.has_liked,
            'language': self.language,
            'self_comment': self.self_comment,
            'ai_reply': self.ai_reply,
            'user_id': self.user_id,
            'fetched_at': self.fetched_at.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }
