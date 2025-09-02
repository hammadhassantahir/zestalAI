import requests
import time


class GoHighLevelError(Exception):
    """Base exception for GoHighLevel API errors"""
    pass


class RateLimitError(GoHighLevelError):
    """Raised when API rate limit is hit"""
    pass


class GoHighLevelAPI:
    BASE_URL = "https://rest.gohighlevel.com/v1"

    def __init__(self, api_key: str, max_retries: int = 3, backoff_factor: float = 2.0):
        """
        :param api_key: Your Location API Key
        :param max_retries: Max retry attempts when hitting rate limit
        :param backoff_factor: Multiplier for exponential backoff (seconds)
        """
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    # ----------------
    # Internal Request
    # ----------------
    def request(self, method, endpoint, params=None, data=None, json=None):
        url = f"{self.BASE_URL}{endpoint}"

        retries = 0
        while True:
            r = requests.request(
                method, url, headers=self.headers, params=params, data=data, json=json
            )

            if r.status_code == 429:  # Rate limit
                if retries < self.max_retries:
                    wait_time = self.backoff_factor * (2 ** retries)
                    print(f"⚠️ Rate limited. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    retries += 1
                    continue
                else:
                    raise RateLimitError("Exceeded API rate limit after retries")

            if not r.ok:
                try:
                    error_data = r.json()
                except ValueError:
                    error_data = r.text
                raise GoHighLevelError(
                    f"API Error {r.status_code}: {error_data}"
                )

            try:
                return r.json()
            except ValueError:
                return r.text

    # ----------------
    # Generic Helpers
    # ----------------
    def get(self, endpoint, params=None):
        return self.request("GET", endpoint, params=params)

    def post(self, endpoint, data=None, json=None):
        return self.request("POST", endpoint, data=data, json=json)

    def put(self, endpoint, data=None, json=None):
        return self.request("PUT", endpoint, data=data, json=json)

    def delete(self, endpoint, params=None):
        return self.request("DELETE", endpoint, params=params)

    # ----------------
    # Contacts
    # ----------------
    def get_contacts(self, limit=20, query=None):
        params = {"limit": limit}
        if query:
            params["query"] = query
        return self.get("/contacts/", params=params)

    def create_contact(self, contact_data: dict):
        return self.post("/contacts/", json=contact_data)

    def update_contact(self, contact_id: str, contact_data: dict):
        return self.put(f"/contacts/{contact_id}", json=contact_data)

    def delete_contact(self, contact_id: str):
        return self.delete(f"/contacts/{contact_id}")

    # ----------------
    # Opportunities
    # ----------------
    def get_opportunities(self, pipeline_id=None):
        params = {}
        if pipeline_id:
            params["pipelineId"] = pipeline_id
        return self.get("/opportunities/", params=params)

    def create_opportunity(self, opportunity_data: dict):
        return self.post("/opportunities/", json=opportunity_data)

    # ----------------
    # Pipelines
    # ----------------
    def get_pipelines(self):
        return self.get("/pipelines/")

    # ----------------
    # Appointments
    # ----------------
    def get_appointments(self, limit=20):
        return self.get("/appointments/", params={"limit": limit})

    def create_appointment(self, appointment_data: dict):
        return self.post("/appointments/", json=appointment_data)

    # ----------------
    # Conversations
    # ----------------
    def get_conversations(self, limit=20):
        return self.get("/conversations/", params={"limit": limit})

    def send_message(self, conversation_id: str, message_data: dict):
        return self.post(f"/conversations/{conversation_id}/messages", json=message_data)

    # ----------------
    # Tags
    # ----------------
    def get_tags(self):
        return self.get("/tags/")

    def create_tag(self, name: str):
        return self.post("/tags/", json={"name": name})

    # ----------------
    # Custom Fields
    # ----------------
    def get_custom_fields(self):
        return self.get("/custom-fields/")

    def create_custom_field(self, field_data: dict):
        return self.post("/custom-fields/", json=field_data)
