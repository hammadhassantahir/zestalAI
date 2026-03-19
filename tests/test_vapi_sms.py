# tests/test_vapi_sms.py
from unittest.mock import MagicMock, patch


def test_send_sms_passes_status_callback():
    """send_sms should forward status_callback to Twilio client."""
    with patch('app.services.twilio_service.Client') as MockClient:
        mock_msg = MagicMock()
        mock_msg.sid = 'SM123'
        mock_msg.status = 'queued'
        mock_msg.from_ = '+1111'
        mock_msg.to = '+2222'
        mock_msg.body = 'hello'
        mock_msg.date_sent = None
        MockClient.return_value.messages.create.return_value = mock_msg

        from flask import Flask
        app = Flask(__name__)
        app.config['TWILIO_ACCOUNT_SID'] = 'ACtest'
        app.config['TWILIO_AUTH_TOKEN'] = 'token'

        with app.app_context():
            from app.services.twilio_service import TwilioService
            svc = TwilioService(account_sid='ACtest', auth_token='token')
            svc.send_sms('+1111', '+2222', 'hello', status_callback='https://example.com/cb')

        MockClient.return_value.messages.create.assert_called_once_with(
            from_='+1111',
            to='+2222',
            body='hello',
            status_callback='https://example.com/cb',
        )
