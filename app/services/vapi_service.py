import logging
import requests
from flask import current_app

logger = logging.getLogger(__name__)


class VapiService:
    BASE_URL = "https://api.vapi.ai"

    def __init__(self, api_key=None):
        self.api_key = api_key or current_app.config.get('VAPI_API_KEY')

    def _request(self, method, path, data=None):
        url = f"{self.BASE_URL}{path}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        resp = requests.request(method, url, headers=headers, json=data, timeout=30)
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            logger.error(f"Vapi {method} {path} failed [{resp.status_code}]: {resp.text[:300]}")
            raise Exception(f"Vapi API error [{resp.status_code}]: {resp.text[:300]}") from e
        return resp.json() if resp.text else {}

    def get_or_create_twilio_credential(self, twilio_account_sid=None, twilio_auth_token=None):
        """Ensure a Twilio credential exists on Vapi. Returns the credential ID."""
        account_sid = twilio_account_sid or current_app.config.get('TWILIO_ACCOUNT_SID')
        auth_token = twilio_auth_token or current_app.config.get('TWILIO_AUTH_TOKEN')

        # Check existing credentials for a matching Twilio one
        credentials = self._request("GET", "/credential")
        for cred in credentials:
            if cred.get('provider') == 'twilio':
                logger.info(f"Found existing Twilio credential: {cred['id']}")
                return cred['id']

        # Create new Twilio credential (Vapi requires all 4 fields)
        payload = {
            "provider": "twilio",
            "apiKey": account_sid,
            "apiSecret": auth_token,
            "accountSid": account_sid,
            "authToken": auth_token,
        }
        result = self._request("POST", "/credential", data=payload)
        logger.info(f"Created Twilio credential on Vapi: {result['id']}")
        return result['id']

    def import_phone_number(self, phone_number, twilio_sid, name=None, twilio_account_sid=None, twilio_auth_token=None):
        account_sid = twilio_account_sid or current_app.config.get('TWILIO_ACCOUNT_SID')
        auth_token = twilio_auth_token or current_app.config.get('TWILIO_AUTH_TOKEN')

        payload = {
            "provider": "twilio",
            "number": phone_number,
            "twilioAccountSid": account_sid,
            "twilioAuthToken": auth_token,
        }
        if name:
            payload["name"] = name
        return self._request("POST", "/phone-number", data=payload)

    def update_phone_number(self, vapi_phone_id, data):
        return self._request("PATCH", f"/phone-number/{vapi_phone_id}", data=data)

    def delete_phone_number(self, vapi_phone_id):
        return self._request("DELETE", f"/phone-number/{vapi_phone_id}")

    def create_assistant(self, payload):
        return self._request("POST", "/assistant", data=payload)

    def get_assistant(self, vapi_assistant_id):
        return self._request("GET", f"/assistant/{vapi_assistant_id}")

    def update_assistant(self, vapi_assistant_id, payload):
        return self._request("PATCH", f"/assistant/{vapi_assistant_id}", data=payload)

    def delete_assistant(self, vapi_assistant_id):
        return self._request("DELETE", f"/assistant/{vapi_assistant_id}")

    def create_call(self, assistant_id, phone_number_id, customer_number, overrides=None, schedule_at=None):
        payload = {
            "assistantId": assistant_id,
            "phoneNumberId": phone_number_id,
            "customer": {
                "number": customer_number,
            },
        }
        if overrides:
            payload["assistantOverrides"] = overrides
        if schedule_at:
            payload["schedulePlan"] = {
                "earliestAt": schedule_at.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            }
        return self._request("POST", "/call/phone", data=payload)

    def get_call(self, vapi_call_id):
        return self._request("GET", f"/call/{vapi_call_id}")

    def list_calls(self, limit=100):
        return self._request("GET", f"/call?limit={limit}")
