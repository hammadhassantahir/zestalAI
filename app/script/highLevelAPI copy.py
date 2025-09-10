# highlevel_api.py
# LeadConnector / HighLevel Private Integrations API v2.0 Python client
# Works with access tokens and location-scoped endpoints.
# Requires: Python 3.8+

from __future__ import annotations
import time
import json
import typing as t
from dataclasses import dataclass
from urllib.parse import urlencode, urljoin

import requests

__all__ = ["LeadConnectorClient", "APIError"]


DEFAULT_BASE_URL = "https://services.leadconnectorhq.com"
DEFAULT_API_VERSION = "2021-07-28"


class APIError(Exception):
    """Raised for non-2xx responses."""
    def __init__(self, status: int, message: str = "", payload: t.Any = None, response: requests.Response | None = None):
        super().__init__(f"[{status}] {message}")
        self.status = status
        self.payload = payload
        self.response = response


@dataclass
class RetryConfig:
    max_retries: int = 4
    base_delay: float = 0.8   # seconds (exponential backoff)
    max_delay: float = 10.0   # cap backoff


class LeadConnectorClient:
    """
    HighLevel / LeadConnector Private Integrations API v2.0 client.

    - Auth: Bearer access token (Private Integrations v2.0).
    - Required header: Version: 2021-07-28
    - Base URL: https://services.leadconnectorhq.com

    Important:
      • Many endpoints are location-scoped (sub-account). Provide `location_id` when needed.
      • For company-scoped or agency-level endpoints, your token must have access.
      • This client exposes convenience wrappers for commonly used endpoints and
        a generic `call()` for anything else in the docs.

    Scopes:
      This file is built to be used with the long list of read/write scopes you shared
      (View/Edit Businesses, Calendars, Contacts, Conversations, Objects, Associations,
      Invoices (incl. Schedules/Templates), Products/Prices/Collections, Payments
      (Orders/Transactions/Custom Providers/Coupons), SaaS Subscriptions, Social Planner,
      Store (Shipping/Settings), Surveys, Users, Workflows, Email Templates/Schedules,
      Funnels/Pages/Page Counts, Opportunities, Tags, Tasks (incl. recurring), Media,
      Redirect URLs / Trigger Links, LC Email (view), Knowledge Base, Voice AI, Blog, etc.)

    If you don’t see a convenience method for a specific endpoint, use `client.call()`.
    """
    BASE_URL = "https://services.leadconnectorhq.com"

    def __init__(self, access_token: str, location_id: str = None):
        self.access_token = access_token
        self.location_id = location_id
        print('***************************************************')
        print(self.access_token)
        print(self.location_id)
        print('***************************************************')

    def _request(self, method, path, params=None, data=None):
        """
        Internal helper for all requests.
        Automatically attaches headers and handles errors.
        """
        url = f"{self.BASE_URL}{path}"
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.access_token}",
            "Version": "2021-07-28",
        }

        # Add LocationId header only if provided
        if self.location_id:
            headers["LocationId"] = self.location_id

        resp = requests.request(
            method, url, headers=headers, params=params, json=data
        )

        # Raise for debugging if error
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            raise Exception(
                f"[{resp.status_code}] Error calling {method} {url}: {resp.text}"
            ) from e

        return resp.json()

    def _sleep(self, attempt: int):
        delay = min(self.retry.base_delay * (2 ** attempt), self.retry.max_delay)
        time.sleep(delay)

    # Generic caller for any documented endpoint (path is like '/contacts', '/calendars/events/appointments', etc.)
    def call(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
        data: dict | None = None,
        files: dict | None = None,
        headers: dict | None = None,
        timeout: float | None = None,
    ):
        return self._request(method, path, params=params, json_body=json, data=data, files=files, headers=headers, timeout=timeout)

    # ------------------------------
    # Utilities
    # ------------------------------
    def set_location_id(self, location_id: str):
        self.location_id = location_id

    def set_company_id(self, company_id: str):
        self.company_id = company_id

    # ✅ Fixed name + behavior
    def get_company_id_from_location(self, location_id: str | None = None) -> dict:
        """
        Get the companyId for a given location (sub-account) ID.
        Returns: {'companyId': '...', 'location': <full location object>}
        """
        loc_id = location_id or self.location_id
        if not loc_id:
            raise ValueError("location_id is required")
        location = self._request("GET", f"/locations/{loc_id}")
        company_id = location.get("companyId") or location.get("company_id")
        if not company_id:
            raise APIError(404, "companyId not found in location payload", payload=location)
        return {"companyId": company_id, "location": location}

    # ------------------------------
    # Companies / Business
    # ------------------------------
    def get_company(self, company_id: str | None = None):
        """
        Get company by ID.
        """
        cid = company_id or self.company_id
        if not cid:
            raise ValueError("company_id is required")
        return self._request("GET", f"/companies/{cid}")

    def get_location(self, location_id: str | None = None):
        """
        Get location (sub-account) by ID.
        """
        loc_id = location_id or self.location_id
        if not loc_id:
            raise ValueError("location_id is required")
        return self._request("GET", f"/locations/{loc_id}")

    # ------------------------------
    # Calendars
    # ------------------------------
    # Calendars list (GET /calendars?locationId=...)
    def list_calendars(self, location_id: str | None = None, **query):
        loc_id = location_id or self.location_id
        if not loc_id:
            raise ValueError("location_id is required")
        params = {"locationId": loc_id, **query}
        return self._request("GET", "/calendars", params=params)

    # Calendar Groups
    def list_calendar_groups(self, location_id: str | None = None, **query):
        loc_id = location_id or self.location_id
        params = {"locationId": loc_id, **query} if loc_id else query
        return self._request("GET", "/calendars/groups", params=params)

    def create_calendar_group(self, payload: dict):
        return self._request("POST", "/calendars/groups", json_body=payload)

    def update_calendar_group(self, group_id: str, payload: dict):
        return self._request("PUT", f"/calendars/groups/{group_id}", json_body=payload)

    def disable_calendar_group(self, group_id: str):
        return self._request("POST", f"/calendars/groups/{group_id}/disable")

    def delete_calendar_group(self, group_id: str):
        return self._request("DELETE", f"/calendars/groups/{group_id}")

    def validate_calendar_group_slug(self, slug: str, location_id: str | None = None):
        loc_id = location_id or self.location_id
        payload = {"slug": slug, "locationId": loc_id}
        return self._request("POST", "/calendars/groups/validateSlug", json_body=payload)

    # Calendar Events (Appointments, Blocks)
    # per docs: POST /calendars/events/appointments
    def create_appointment(self, payload: dict):
        return self._request("POST", "/calendars/events/appointments", json_body=payload)

    def update_appointment(self, appointment_id: str, payload: dict):
        return self._request("PUT", f"/calendars/events/appointments/{appointment_id}", json_body=payload)

    def get_appointment(self, appointment_id: str):
        return self._request("GET", f"/calendars/events/appointments/{appointment_id}")

    def list_calendar_events(self, calendar_id: str, **query):
        params = {"calendarId": calendar_id, **query}
        return self._request("GET", "/calendars/events", params=params)

    def get_blocked_slots(self, calendar_id: str, **query):
        params = {"calendarId": calendar_id, **query}
        return self._request("GET", "/calendars/events/blockedSlots", params=params)

    def create_block_slot(self, payload: dict):
        return self._request("POST", "/calendars/events/blockedSlots", json_body=payload)

    def update_block_slot(self, block_id: str, payload: dict):
        return self._request("PUT", f"/calendars/events/blockedSlots/{block_id}", json_body=payload)

    def delete_event(self, event_id: str):
        return self._request("DELETE", f"/calendars/events/{event_id}")

    # Appointment Notes
    def list_appointment_notes(self, appointment_id: str):
        return self._request("GET", f"/calendars/events/appointments/{appointment_id}/notes")

    def create_appointment_note(self, appointment_id: str, payload: dict):
        return self._request("POST", f"/calendars/events/appointments/{appointment_id}/notes", json_body=payload)

    # Calendar Resources: Rooms & Equipment
    def list_calendar_resources(self, location_id: str | None = None, **query):
        loc_id = location_id or self.location_id
        params = {"locationId": loc_id, **query} if loc_id else query
        return self._request("GET", "/calendars/resources", params=params)

    def create_calendar_resource(self, payload: dict):
        return self._request("POST", "/calendars/resources", json_body=payload)

    def update_calendar_resource(self, resource_id: str, payload: dict):
        return self._request("PUT", f"/calendars/resources/{resource_id}", json_body=payload)

    def delete_calendar_resource(self, resource_id: str):
        return self._request("DELETE", f"/calendars/resources/{resource_id}")

    # ------------------------------
    # Contacts
    # ------------------------------
    def get_contact(self, contact_id: str):
        return self._request("GET", f"/contacts/{contact_id}")

    def update_contact(self, contact_id: str, payload: dict):
        return self._request("PUT", f"/contacts/{contact_id}", json_body=payload)

    def delete_contact(self, contact_id: str):
        return self._request("DELETE", f"/contacts/{contact_id}")

    def upsert_contact(self, payload: dict):
        return self._request("POST", "/contacts/upsert", json_body=payload)

    def create_contact(self, payload: dict):
        return self._request("POST", "/contacts/", json_body=payload)

    def list_contacts(self, **query):
        print('***************************************************')
        print(query)
        print('***************************************************')
        return self._request("GET", "/contacts/", params=query)

    def list_contacts_by_business(self, business_id: str, **query):
        params = {"businessId": business_id, **query}
        return self._request("GET", "/contacts/business", params=params)

    # Contacts: Search / Bulk / etc. (docs offer complex query)
    def search_contacts(self, payload: dict):
        return self._request("POST", "/contacts/search", json_body=payload)

    # Contact Tags
    def add_tag_to_contact(self, contact_id: str, tag: str):
        return self._request("POST", f"/contacts/{contact_id}/tags", json_body={"tag": tag})

    def remove_tag_from_contact(self, contact_id: str, tag: str):
        return self._request("DELETE", f"/contacts/{contact_id}/tags/{tag}")

    # ------------------------------
    # Conversations + Messages
    # ------------------------------
    def get_conversation(self, conversation_id: str):
        return self._request("GET", f"/conversations/{conversation_id}")

    def update_conversation(self, conversation_id: str, payload: dict):
        return self._request("PUT", f"/conversations/{conversation_id}", json_body=payload)

    def delete_conversation(self, conversation_id: str):
        return self._request("DELETE", f"/conversations/{conversation_id}")

    def create_conversation(self, payload: dict):
        return self._request("POST", "/conversations", json_body=payload)

    # Messages
    def export_messages_by_location(self, location_id: str | None = None, **query):
        loc_id = location_id or self.location_id
        if not loc_id:
            raise ValueError("location_id is required")
        params = {"locationId": loc_id, **query}
        return self._request("GET", "/conversations/messages/export", params=params)

    def get_message(self, message_id: str):
        return self._request("GET", f"/conversations/messages/{message_id}")

    def get_messages_by_conversation(self, conversation_id: str, **query):
        return self._request("GET", f"/conversations/{conversation_id}/messages", params=query)

    def send_message(self, payload: dict):
        return self._request("POST", "/conversations/messages", json_body=payload)

    def add_inbound_message(self, payload: dict):
        return self._request("POST", "/conversations/messages/inbound", json_body=payload)

    def add_external_outbound_call(self, payload: dict):
        return self._request("POST", "/conversations/messages/externalCall", json_body=payload)

    def cancel_scheduled_message(self, message_id: str):
        return self._request("POST", f"/conversations/messages/{message_id}/cancel")

    def upload_message_attachment(self, file_path: str):
        with open(file_path, "rb") as f:
            files = {"fileAttachment": (file_path.split("/")[-1], f)}
            return self._request("POST", "/conversations/messages/attachments", files=files)

    def update_message_status(self, payload: dict):
        return self._request("POST", "/conversations/messages/status", json_body=payload)

    def get_recording_by_message_id(self, message_id: str):
        return self._request("GET", f"/conversations/messages/{message_id}/recording")

    def get_transcription_by_message_id(self, message_id: str):
        return self._request("GET", f"/conversations/messages/{message_id}/transcription")

    def download_transcription_by_message_id(self, message_id: str):
        # Returns file bytes
        return self._request("GET", f"/conversations/messages/{message_id}/transcription/download")

    # ------------------------------
    # Invoices (Invoice / Template / Schedule / Estimate / Text2Pay)
    # ------------------------------
    def generate_invoice_number(self, location_id: str | None = None):
        loc_id = location_id or self.location_id
        params = {"locationId": loc_id} if loc_id else None
        return self._request("GET", "/invoices/generateNumber", params=params)

    def get_invoice(self, invoice_id: str):
        return self._request("GET", f"/invoices/{invoice_id}")

    def update_invoice(self, invoice_id: str, payload: dict):
        return self._request("PUT", f"/invoices/{invoice_id}", json_body=payload)

    def delete_invoice(self, invoice_id: str):
        return self._request("DELETE", f"/invoices/{invoice_id}")

    def update_invoice_late_fees(self, invoice_id: str, payload: dict):
        return self._request("PUT", f"/invoices/{invoice_id}/lateFees", json_body=payload)

    def void_invoice(self, invoice_id: str):
        return self._request("POST", f"/invoices/{invoice_id}/void")

    def send_invoice(self, invoice_id: str, payload: dict | None = None):
        return self._request("POST", f"/invoices/{invoice_id}/send", json_body=payload or {})

    def record_manual_payment(self, invoice_id: str, payload: dict):
        return self._request("POST", f"/invoices/{invoice_id}/payments/manual", json_body=payload)

    def update_invoice_last_visited_at(self, invoice_id: str, timestamp_iso: str):
        return self._request("POST", f"/invoices/{invoice_id}/lastVisitedAt", json_body={"timestamp": timestamp_iso})

    def create_invoice(self, payload: dict):
        return self._request("POST", "/invoices", json_body=payload)

    def list_invoices(self, **query):
        return self._request("GET", "/invoices", params=query)

    # Invoice Templates
    def create_invoice_template(self, payload: dict):
        return self._request("POST", "/invoices/templates", json_body=payload)

    def list_invoice_templates(self, **query):
        return self._request("GET", "/invoices/templates", params=query)

    def get_invoice_template(self, template_id: str):
        return self._request("GET", f"/invoices/templates/{template_id}")

    def update_invoice_template(self, template_id: str, payload: dict):
        return self._request("PUT", f"/invoices/templates/{template_id}", json_body=payload)

    def delete_invoice_template(self, template_id: str):
        return self._request("DELETE", f"/invoices/templates/{template_id}")

    def update_template_late_fees(self, template_id: str, payload: dict):
        return self._request("PUT", f"/invoices/templates/{template_id}/lateFees", json_body=payload)

    # Invoice Schedules
    def create_invoice_schedule(self, payload: dict):
        return self._request("POST", "/invoices/schedules", json_body=payload)

    def list_invoice_schedules(self, **query):
        return self._request("GET", "/invoices/schedules", params=query)

    def get_invoice_schedule(self, schedule_id: str):
        return self._request("GET", f"/invoices/schedules/{schedule_id}")

    def update_invoice_schedule(self, schedule_id: str, payload: dict):
        return self._request("PUT", f"/invoices/schedules/{schedule_id}", json_body=payload)

    def delete_invoice_schedule(self, schedule_id: str):
        return self._request("DELETE", f"/invoices/schedules/{schedule_id}")

    def update_recurring_invoice_on_schedule(self, schedule_id: str, payload: dict):
        return self._request("PUT", f"/invoices/schedules/{schedule_id}/recurring", json_body=payload)

    def start_sending_scheduled_invoice(self, schedule_id: str, payload: dict | None = None):
        return self._request("POST", f"/invoices/schedules/{schedule_id}/start", json_body=payload or {})

    def manage_schedule_auto_payment(self, schedule_id: str, payload: dict):
        return self._request("POST", f"/invoices/schedules/{schedule_id}/autoPayment", json_body=payload)

    def cancel_scheduled_invoice(self, schedule_id: str, payload: dict | None = None):
        return self._request("POST", f"/invoices/schedules/{schedule_id}/cancel", json_body=payload or {})

    # ------------------------------
    # Payments (Orders / Transactions / Subscriptions / Coupons / Custom Providers)
    # ------------------------------
    def list_orders(self, **query):
        return self._request("GET", "/payments/orders", params=query)

    def get_order(self, order_id: str):
        return self._request("GET", f"/payments/orders/{order_id}")

    def record_order_payment(self, order_id: str, payload: dict):
        return self._request("POST", f"/payments/orders/{order_id}/payment", json_body=payload)

    def list_transactions(self, **query):
        return self._request("GET", "/payments/transactions", params=query)

    def get_transaction(self, transaction_id: str):
        return self._request("GET", f"/payments/transactions/{transaction_id}")

    # ------------------------------
    # Products / Prices / Collections / Inventory
    # ------------------------------
    def list_products(self, **query):
        return self._request("GET", "/products", params=query)

    def create_product(self, payload: dict):
        return self._request("POST", "/products", json_body=payload)

    def get_product(self, product_id: str):
        return self._request("GET", f"/products/{product_id}")

    def update_product(self, product_id: str, payload: dict):
        return self._request("PUT", f"/products/{product_id}", json_body=payload)

    def delete_product(self, product_id: str):
        return self._request("DELETE", f"/products/{product_id}")

    def bulk_update_products(self, payload: dict):
        return self._request("POST", "/products/bulkUpdate", json_body=payload)

    def bulk_edit_products_and_prices(self, payload: dict):
        return self._request("POST", "/products/bulkEdit", json_body=payload)

    # Prices for a product
    def create_price(self, product_id: str, payload: dict):
        return self._request("POST", f"/products/{product_id}/prices", json_body=payload)

    def list_prices(self, product_id: str, **query):
        return self._request("GET", f"/products/{product_id}/prices", params=query)

    def get_price(self, product_id: str, price_id: str):
        return self._request("GET", f"/products/{product_id}/prices/{price_id}")

    def update_price(self, product_id: str, price_id: str, payload: dict):
        return self._request("PUT", f"/products/{product_id}/prices/{price_id}", json_body=payload)

    def delete_price(self, product_id: str, price_id: str):
        return self._request("DELETE", f"/products/{product_id}/prices/{price_id}")

    # Inventory
    def list_inventory(self, **query):
        return self._request("GET", "/products/inventory", params=query)

    def update_inventory(self, payload: dict):
        return self._request("PUT", "/products/inventory", json_body=payload)

    # Collections
    def fetch_collections(self, **query):
        return self._request("GET", "/products/collections", params=query)

    def create_collection(self, payload: dict):
        return self._request("POST", "/products/collections", json_body=payload)

    def get_collection(self, collection_id: str):
        return self._request("GET", f"/products/collections/{collection_id}")

    def update_collection(self, collection_id: str, payload: dict):
        return self._request("PUT", f"/products/collections/{collection_id}", json_body=payload)

    def delete_collection(self, collection_id: str):
        return self._request("DELETE", f"/products/collections/{collection_id}")

    # ------------------------------
    # Funnels (pages, counts)
    # ------------------------------
    def list_funnels(self, location_id: str | None = None, **query):
        loc_id = location_id or self.location_id
        params = {"locationId": loc_id, **query} if loc_id else query
        return self._request("GET", "/funnels", params=params)

    def list_funnel_pages(self, funnel_id: str, **query):
        return self._request("GET", f"/funnels/{funnel_id}/pages", params=query)

    def get_funnel_page_counts(self, funnel_id: str):
        return self._request("GET", f"/funnels/{funnel_id}/pageCounts")

    # ------------------------------
    # Opportunities (pipelines / stages commonly required)
    # ------------------------------
    def list_opportunities(self, **query):
        return self._request("GET", "/opportunities/", params=query)

    def create_opportunity(self, payload: dict):
        return self._request("POST", "/opportunities/", json_body=payload)

    def update_opportunity(self, opportunity_id: str, payload: dict):
        return self._request("PUT", f"/opportunities/{opportunity_id}", json_body=payload)

    # ------------------------------
    # Custom Fields V2 (Location-scoped)
    # ------------------------------
    def list_custom_fields(self, location_id: str | None = None):
        loc_id = location_id or self.location_id
        if not loc_id:
            raise ValueError("location_id is required")
        return self._request("GET", f"/locations/{loc_id}/customFields")

    def create_custom_field(self, location_id: str | None = None, payload: dict | None = None):
        loc_id = location_id or self.location_id
        return self._request("POST", f"/locations/{loc_id}/customFields", json_body=payload or {})

    def update_custom_field(self, location_id: str | None = None, field_id: str | None = None, payload: dict | None = None):
        loc_id = location_id or self.location_id
        return self._request("PUT", f"/locations/{loc_id}/customFields/{field_id}", json_body=payload or {})

    # ------------------------------
    # Tags
    # ------------------------------
    def list_tags(self, location_id: str | None = None):
        loc_id = location_id or self.location_id
        params = {"locationId": loc_id} if loc_id else None
        return self._request("GET", "/tags", params=params)

    # ------------------------------
    # Tasks (and recurring tasks helpers)
    # ------------------------------
    def list_tasks(self, **query):
        return self._request("GET", "/tasks", params=query)

    def create_task(self, payload: dict):
        return self._request("POST", "/tasks", json_body=payload)

    def update_task(self, task_id: str, payload: dict):
        return self._request("PUT", f"/tasks/{task_id}", json_body=payload)

    def delete_task(self, task_id: str):
        return self._request("DELETE", f"/tasks/{task_id}")

    # ------------------------------
    # Media Library
    # ------------------------------
    def list_media(self, **query):
        return self._request("GET", "/medias", params=query)

    def upload_media(self, file_path: str, **meta):
        with open(file_path, "rb") as f:
            files = {"file": (file_path.split("/")[-1], f)}
            data = meta or {}
            return self._request("POST", "/medias", files=files, data=data)

    def delete_media(self, media_id: str):
        return self._request("DELETE", f"/medias/{media_id}")

    # ------------------------------
    # Surveys
    # ------------------------------
    def list_surveys(self, **query):
        return self._request("GET", "/surveys", params=query)

    # ------------------------------
    # Users
    # ------------------------------
    def list_users(self, **query):
        return self._request("GET", "/users", params=query)

    # ------------------------------
    # Workflows
    # ------------------------------
    def list_workflows(self, **query):
        return self._request("GET", "/workflows", params=query)

    # ------------------------------
    # Trigger Links / Redirect URLs
    # ------------------------------
    def list_trigger_links(self, **query):
        return self._request("GET", "/links", params=query)

    def create_trigger_link(self, payload: dict):
        return self._request("POST", "/links", json_body=payload)

    def update_trigger_link(self, link_id: str, payload: dict):
        return self._request("PUT", f"/links/{link_id}", json_body=payload)

    def delete_trigger_link(self, link_id: str):
        return self._request("DELETE", f"/links/{link_id}")
