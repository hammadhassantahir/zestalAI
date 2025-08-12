from flask import current_app
from flask_mail import Message
from ..extensions import mail

def send_verification_email(user):
    """Send email verification link to user."""
    msg = Message(
        'Verify your email',
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[user.email]
    )
    verification_url = f"{current_app.config['BASE_URL']}/api/auth/verify/{user.code}"
    msg.body = f'''Hello {user.first_name},

Please click the following link to verify your email:
{verification_url}

If you did not create an account, please ignore this email.

Best regards,
ZestalAI Team
'''
    mail.send(msg)

def send_reset_password_email(user):
    """Send password reset link to user."""
    msg = Message(
        'Password Reset Request',
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[user.email]
    )
    reset_url = f"{current_app.config['BASE_URL']}/api/auth/reset/{user.code}"
    msg.body = f'''Hello {user.first_name},

You have requested to reset your password. Please click the following link to reset your password:
{reset_url}

If you did not request a password reset, please ignore this email.

Best regards,
ZestalAI Team
'''
    mail.send(msg)
