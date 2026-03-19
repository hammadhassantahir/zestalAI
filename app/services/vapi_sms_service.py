import logging
import requests
from flask import current_app
from .language_service import SUPPORTED_LANGUAGES

logger = logging.getLogger(__name__)

VAPI_BASE_URL = "https://api.vapi.ai"


def _lang_name(lang_code):
    for entry in SUPPORTED_LANGUAGES:
        if entry['code'] == lang_code:
            return entry['name']
    return lang_code


class VapiSmsService:

    def __init__(self, api_key=None):
        self.api_key = api_key or current_app.config.get('VAPI_API_KEY')
        self.model = current_app.config.get('VAPI_SMS_MODEL', 'gpt-4o-mini')

    def generate(self, body: str, language: str) -> str:
        lang_name = _lang_name(language)
        user_content = f"{body}\n\nTranslate to {lang_name}. Keep it natural and concise for SMS."

        payload = {
            "assistant": {
                "model": {
                    "provider": "openai",
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an SMS assistant. Translate and adapt the given message into a concise SMS.",
                        }
                    ],
                }
            },
            "input": user_content,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        resp = requests.request(
            "POST",
            f"{VAPI_BASE_URL}/chat",
            headers=headers,
            json=payload,
            timeout=30,
        )
        try:
            resp.raise_for_status()
        except Exception:
            logger.error(f"Vapi chat failed [{resp.status_code}]: {resp.text[:300]}")
            raise Exception(f"Vapi SMS generation failed [{resp.status_code}]")

        data = resp.json()
        output = data.get('output', [])
        for msg in output:
            if msg.get('role') == 'assistant' and msg.get('content'):
                return msg['content'].strip()

        logger.error(f"Unexpected Vapi chat response: {data}")
        raise Exception("Vapi SMS generation returned no content")
