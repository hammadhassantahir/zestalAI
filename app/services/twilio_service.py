import logging
import re
from flask import current_app
from twilio.rest import Client

logger = logging.getLogger(__name__)


def _clean_twilio_error(e):
    raw = re.sub(r'\x1b\[[0-9;]*m', '', str(e)).strip()
    match = re.search(r'Unable to create record:\s*(.+?)(?:\n|$)', raw)
    if match:
        return match.group(1).strip()
    # try generic "Twilio returned" block
    match = re.search(r'Twilio returned the following information:\s*(.+?)(?:\n|$)', raw)
    if match:
        return match.group(1).strip()
    # fallback: first non-empty line after stripping
    lines = [l.strip() for l in raw.splitlines() if l.strip()]
    return lines[-1] if lines else raw


class TwilioService:

    def __init__(self, account_sid=None, auth_token=None):
        self.account_sid = account_sid or current_app.config.get('TWILIO_ACCOUNT_SID')
        self.auth_token = auth_token or current_app.config.get('TWILIO_AUTH_TOKEN')
        self.client = Client(self.account_sid, self.auth_token)

    def search_available_numbers(self, country_code='US', area_code=None, limit=10):
        try:
            kwargs = {'limit': limit}
            if area_code:
                kwargs['area_code'] = area_code

            available = self.client.available_phone_numbers(country_code).local.list(**kwargs)

            numbers = []
            for num in available:
                numbers.append({
                    'phone_number': num.phone_number,
                    'friendly_name': num.friendly_name,
                    'capabilities': num.capabilities,
                    'locality': num.locality,
                    'region': num.region,
                    'iso_country': num.iso_country,
                })

            return {'success': True, 'numbers': numbers}
        except Exception as e:
            logger.error(f"Twilio search error: {str(e)}")
            return {'error': _clean_twilio_error(e)}

    def buy_number(self, phone_number):
        try:
            purchased = self.client.incoming_phone_numbers.create(
                phone_number=phone_number
            )
            return {
                'success': True,
                'sid': purchased.sid,
                'phone_number': purchased.phone_number,
                'friendly_name': purchased.friendly_name,
                'capabilities': {
                    'voice': purchased.capabilities.get('voice', False),
                    'sms': purchased.capabilities.get('sms', False),
                    'mms': purchased.capabilities.get('mms', False),
                },
            }
        except Exception as e:
            logger.error(f"Twilio buy error: {str(e)}")
            return {'error': _clean_twilio_error(e)}

    def release_number(self, twilio_sid):
        try:
            self.client.incoming_phone_numbers(twilio_sid).delete()
            return {'success': True}
        except Exception as e:
            logger.error(f"Twilio release error: {str(e)}")
            return {'error': _clean_twilio_error(e)}

    def send_sms(self, from_number, to_number, body, status_callback=None):
        try:
            kwargs = dict(from_=from_number, to=to_number, body=body)
            if status_callback:
                kwargs['status_callback'] = status_callback
            msg = self.client.messages.create(**kwargs)
            return {
                'success': True,
                'sid': msg.sid,
                'status': msg.status,
                'from': msg.from_,
                'to': msg.to,
                'body': msg.body,
                'date_sent': msg.date_sent.isoformat() if msg.date_sent else None,
            }
        except Exception as e:
            logger.error(f"Twilio send SMS error: {str(e)}")
            return {'error': _clean_twilio_error(e)}

    def get_sms(self, message_sid):
        try:
            msg = self.client.messages(message_sid).fetch()
            return {
                'success': True,
                'sid': msg.sid,
                'status': msg.status,
                'from': msg.from_,
                'to': msg.to,
                'body': msg.body,
                'date_sent': msg.date_sent.isoformat() if msg.date_sent else None,
                'price': msg.price,
                'error_code': msg.error_code,
                'error_message': msg.error_message,
            }
        except Exception as e:
            logger.error(f"Twilio get SMS error: {str(e)}")
            return {'error': _clean_twilio_error(e)}

    def list_sms(self, from_number=None, to_number=None, limit=50):
        try:
            kwargs = {'limit': limit}
            if from_number:
                kwargs['from_'] = from_number
            if to_number:
                kwargs['to'] = to_number
            messages = self.client.messages.list(**kwargs)
            return {
                'success': True,
                'messages': [{
                    'sid': m.sid,
                    'status': m.status,
                    'from': m.from_,
                    'to': m.to,
                    'body': m.body,
                    'direction': m.direction,
                    'date_sent': m.date_sent.isoformat() if m.date_sent else None,
                    'price': m.price,
                } for m in messages],
            }
        except Exception as e:
            logger.error(f"Twilio list SMS error: {str(e)}")
            return {'error': _clean_twilio_error(e)}

    def list_account_numbers(self, limit=200):
        try:
            numbers = self.client.incoming_phone_numbers.list(limit=limit)
            result = []
            for num in numbers:
                result.append({
                    'sid': num.sid,
                    'phone_number': num.phone_number,
                    'friendly_name': num.friendly_name,
                    'status': num.status,
                })
            return {'success': True, 'numbers': result}
        except Exception as e:
            logger.error(f"Twilio list error: {str(e)}")
            return {'error': _clean_twilio_error(e)}
