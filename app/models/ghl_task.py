from datetime import datetime
from ..extensions import db


class GHLTask(db.Model):
    """Local mirror of GoHighLevel tasks for fast querying."""
    __tablename__ = 'ghl_tasks'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    ghl_task_id = db.Column(db.String(255), unique=True, nullable=False)
    ghl_contact_id = db.Column(db.String(255), nullable=False)

    # Task fields
    title = db.Column(db.String(500), nullable=True)
    body = db.Column(db.Text, nullable=True)
    due_date = db.Column(db.DateTime, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    assigned_to = db.Column(db.String(255), nullable=True)

    # Cached contact info (avoids extra API calls on local routes)
    contact_first_name = db.Column(db.String(100), nullable=True)
    contact_last_name = db.Column(db.String(100), nullable=True)
    contact_email = db.Column(db.String(255), nullable=True)
    contact_phone = db.Column(db.String(50), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = db.relationship('User', backref='ghl_tasks')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'ghl_task_id': self.ghl_task_id,
            'ghl_contact_id': self.ghl_contact_id,
            'title': self.title,
            'body': self.body,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed': self.completed,
            'assigned_to': self.assigned_to,
            'contact': {
                'id': self.ghl_contact_id,
                'firstName': self.contact_first_name,
                'lastName': self.contact_last_name,
                'email': self.contact_email,
                'phone': self.contact_phone,
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_ghl_response(cls, ghl_data, user_id, contact_id, contact_info=None):
        """
        Build a GHLTask instance from a GHL API response dict.

        Args:
            ghl_data: The task dict returned by GHL API
            user_id: Local user ID
            contact_id: GHL contact ID
            contact_info: Optional dict with firstName, lastName, email, phone
        """
        due_date = None
        if ghl_data.get('dueDate'):
            try:
                due_date = datetime.fromisoformat(
                    ghl_data['dueDate'].replace('Z', '+00:00')
                )
            except (ValueError, AttributeError):
                pass

        task = cls(
            user_id=user_id,
            ghl_task_id=ghl_data.get('id', ''),
            ghl_contact_id=contact_id,
            title=ghl_data.get('title', ''),
            body=ghl_data.get('body', ''),
            due_date=due_date,
            completed=ghl_data.get('completed', False),
            assigned_to=ghl_data.get('assignedTo', ''),
        )

        if contact_info:
            task.contact_first_name = contact_info.get('firstName', '')
            task.contact_last_name = contact_info.get('lastName', '')
            task.contact_email = contact_info.get('email', '')
            task.contact_phone = contact_info.get('phone', '')

        return task

    def update_from_ghl(self, ghl_data):
        """Update local fields from a GHL API response dict."""
        if 'title' in ghl_data:
            self.title = ghl_data['title']
        if 'body' in ghl_data:
            self.body = ghl_data['body']
        if 'dueDate' in ghl_data:
            try:
                self.due_date = datetime.fromisoformat(
                    ghl_data['dueDate'].replace('Z', '+00:00')
                )
            except (ValueError, AttributeError):
                pass
        if 'completed' in ghl_data:
            self.completed = ghl_data['completed']
        if 'assignedTo' in ghl_data:
            self.assigned_to = ghl_data['assignedTo']
