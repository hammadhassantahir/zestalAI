"""
GoHighLevel (LeadConnectorHQ) Python Client
Private Integrations API v2.0
"""

import requests


class LeadConnectorClient:
    BASE_URL = "https://services.leadconnectorhq.com"

    def __init__(self, access_token: str, location_id: str = None):
        self.access_token = access_token
        self.location_id = location_id

    def _request(self, method, path, params=None, data=None):
        url = f"{self.BASE_URL}{path}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "Version": "2021-07-28",
        }

        # Ensure query params exist
        params = params or {}

        # Always add locationId as a query param if available
        if self.location_id and "locationId" not in params:
            params["locationId"] = self.location_id

        resp = requests.request(
            method, url, headers=headers, params=params, json=data
        )

        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            raise Exception(
                f"[{resp.status_code}] Error calling {method} {url}: {resp.text}"
            ) from e

        return resp.json()

    def _request2(self, method, path, params=None, data=None):
        url = f"{self.BASE_URL}{path}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "Version": "2021-07-28",
        }

        if self.location_id:
            headers["LocationId"] = self.location_id

        resp = requests.request(
            method, url, headers=headers, params=params, json=data
        )

        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            raise Exception(
                f"[{resp.status_code}] Error calling {method} {url}: {resp.text}"
            ) from e

        return resp.json()

    # =====================
    # Locations & Companies
    # =====================
    def get_location(self, location_id: str = None):
        loc_id = location_id or self.location_id
        return self._request("GET", f"/locations/{loc_id}")

    def get_company_id_from_location(self, location_id: str = None):
        location = self.get_location(location_id)
        if "companyId" not in location:
            raise Exception("companyId not found in location payload")
        return location["companyId"]

    # ========
    # Contacts
    # ========
    def list_contacts(self, **query):
        return self._request("GET", "/contacts/", params=query)

    def get_contact(self, contact_id: str):
        return self._request("GET", f"/contacts/{contact_id}")

    def create_contact(self, data: dict):
        return self._request("POST", "/contacts/", data=data)

    def update_contact(self, contact_id: str, data: dict):
        return self._request("PUT", f"/contacts/{contact_id}", data=data)

    def delete_contact(self, contact_id: str):
        return self._request("DELETE", f"/contacts/{contact_id}")

    # =========
    # Campaigns
    # =========
    def list_campaigns(self, **query):
        return self._request("GET", "/campaigns/", params=query)

    # ============
    # Conversations
    # ============
    def list_conversations(self, **query):
        return self._request("GET", "/conversations/", params=query)

    def get_conversation(self, conversation_id: str):
        return self._request("GET", f"/conversations/{conversation_id}")

    def send_conversation_message(self, data: dict):
        return self._request("POST", "/conversations/messages", data=data)

    # =======
    # Invoices
    # =======
    def list_invoices(self, **query):
        return self._request("GET", "/invoices/", params=query)

    def create_invoice(self, data: dict):
        return self._request("POST", "/invoices/", data=data)

    def update_invoice(self, invoice_id: str, data: dict):
        return self._request("PUT", f"/invoices/{invoice_id}", data=data)

    def delete_invoice(self, invoice_id: str):
        return self._request("DELETE", f"/invoices/{invoice_id}")

    # =====
    # Tasks
    # =====
    def list_tasks(self, **query):
        return self._request("GET", "/tasks/", params=query)

    def create_task(self, data: dict):
        return self._request("POST", "/tasks/", data=data)

    def update_task(self, task_id: str, data: dict):
        return self._request("PUT", f"/tasks/{task_id}", data=data)

    def delete_task(self, task_id: str):
        return self._request("DELETE", f"/tasks/{task_id}")

    # ====
    # Tags
    # ====
    def list_tags(self, **query):
        return self._request("GET", "/tags/", params=query)

    def create_tag(self, data: dict):
        return self._request("POST", "/tags/", data=data)

    def delete_tag(self, tag_id: str):
        return self._request("DELETE", f"/tags/{tag_id}")

    # =========
    # Workflows
    # =========
    def list_workflows(self, **query):
        return self._request("GET", "/workflows/", params=query)

    # =====
    # Users
    # =====
    def list_users(self, **query):
        return self._request("GET", "/users/", params=query)

    def get_user(self, user_id: str):
        return self._request("GET", f"/users/{user_id}")

    # =========
    # Calendars
    # =========
    def list_calendars(self, **query):
        return self._request("GET", "/calendars/", params=query)

    def get_calendar(self, calendar_id: str):
        return self._request("GET", f"/calendars/{calendar_id}")

    def create_calendar(self, data: dict):
        return self._request("POST", "/calendars/", data=data)

    def update_calendar(self, calendar_id: str, data: dict):
        return self._request("PUT", f"/calendars/{calendar_id}", data=data)

    def delete_calendar(self, calendar_id: str):
        return self._request("DELETE", f"/calendars/{calendar_id}")