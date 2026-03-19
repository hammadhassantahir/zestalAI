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


def test_vapi_sms_generate_translates_body():
    """generate() should call Vapi chat and return the message text."""
    with patch('app.services.vapi_sms_service.requests.request') as mock_req:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = '{"output": [{"role": "assistant", "content": "Bonjour le monde"}]}'
        mock_resp.json.return_value = {"output": [{"role": "assistant", "content": "Bonjour le monde"}]}
        mock_resp.raise_for_status = MagicMock()
        mock_req.return_value = mock_resp

        from flask import Flask
        app = Flask(__name__)
        app.config['VAPI_API_KEY'] = 'test-key'
        app.config['VAPI_SMS_MODEL'] = 'gpt-4o-mini'

        with app.app_context():
            from app.services.vapi_sms_service import VapiSmsService
            svc = VapiSmsService()
            result = svc.generate('Hello world', 'fr-FR')

        assert result == 'Bonjour le monde'


def test_vapi_sms_generate_raises_on_error():
    """generate() raises Exception on Vapi API error."""
    with patch('app.services.vapi_sms_service.requests.request') as mock_req:
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.text = 'Internal error'
        mock_resp.raise_for_status.side_effect = Exception('HTTP Error')
        mock_req.return_value = mock_resp

        from flask import Flask
        app = Flask(__name__)
        app.config['VAPI_API_KEY'] = 'test-key'
        app.config['VAPI_SMS_MODEL'] = 'gpt-4o-mini'

        with app.app_context():
            from app.services.vapi_sms_service import VapiSmsService
            svc = VapiSmsService()
            try:
                svc.generate('hello', 'fr-FR')
                assert False, 'should have raised'
            except Exception as e:
                assert 'Vapi SMS generation failed' in str(e)
