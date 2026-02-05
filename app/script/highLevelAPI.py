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

        # Check if we should skip adding locationId (some endpoints infer from token)
        skip_location = params.pop('_skip_location', False)
        
        # Add locationId as a query param if available and not skipped
        if self.location_id and not skip_location and "locationId" not in params:
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

    def create_location(self, data: dict):
        """Create a new sub-account/location."""
        try:
            response = self._request("POST", "/locations/", data=data)
            return response
        except Exception as e:
            raise Exception(f"Error creating location: {str(e)}")

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
    # Tasks (Note: Tasks are per contact in GHL)
    # =====
    def list_tasks(self, contact_id: str, **query):
        """List tasks for a specific contact"""
        return self._request("GET", f"/contacts/{contact_id}/tasks/", params=query)

    def get_task(self, contact_id: str, task_id: str):
        """Get a specific task"""
        return self._request("GET", f"/contacts/{contact_id}/tasks/{task_id}")

    def create_task(self, contact_id: str, data: dict):
        """Create a task for a contact"""
        return self._request("POST", f"/contacts/{contact_id}/tasks/", data=data)

    def update_task(self, contact_id: str, task_id: str, data: dict):
        """Update a task"""
        return self._request("PUT", f"/contacts/{contact_id}/tasks/{task_id}", data=data)

    def delete_task(self, contact_id: str, task_id: str):
        """Delete a task"""
        return self._request("DELETE", f"/contacts/{contact_id}/tasks/{task_id}")

    def complete_task(self, contact_id: str, task_id: str, completed: bool = True):
        """Mark a task as completed or incomplete"""
        return self._request("PUT", f"/contacts/{contact_id}/tasks/{task_id}/completed", data={"completed": completed})

    # ====
    # Tags (under location)
    # ====
    def list_tags(self, **query):
        """List tags for the location"""
        return self._request("GET", f"/locations/{self.location_id}/tags/", params=query)

    def create_tag(self, data: dict):
        """Create a tag"""
        return self._request("POST", f"/locations/{self.location_id}/tags/", data=data)

    def delete_tag(self, tag_id: str):
        """Delete a tag"""
        return self._request("DELETE", f"/locations/{self.location_id}/tags/{tag_id}")

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

    # =========
    # Pipelines
    # =========
    def list_pipelines(self, **query):
        """GET /opportunities/pipelines - Get all pipelines"""
        return self._request("GET", "/opportunities/pipelines", params=query)

    def get_pipeline_stages(self, pipeline_id: str):
        """Get stages for a specific pipeline (from pipeline data)"""
        pipelines = self.list_pipelines()
        if 'pipelines' in pipelines:
            for pipeline in pipelines['pipelines']:
                if pipeline.get('id') == pipeline_id:
                    return {'stages': pipeline.get('stages', [])}
        return {'stages': []}

    # =============
    # Opportunities
    # =============
    def search_opportunities(self, **query):
        """GET /opportunities/search - Search opportunities with filters
        
        Supported query params:
        - pipeline_id: Filter by pipeline
        - pipeline_stage_id: Filter by stage
        - status: Filter by status (open, won, lost, abandoned, all)
        - contact_id: Filter by contact
        - limit: Limit results (max 100, default 20)
        - page: Page number
        
        Note: GHL API requires location_id (snake_case), not locationId (camelCase)
        """
        params = dict(query)
        # Add location_id (snake_case) as required by this endpoint
        params['location_id'] = self.location_id
        # Skip adding locationId (camelCase) - this endpoint wants snake_case
        params['_skip_location'] = True
        return self._request("GET", "/opportunities/search", params=params)

    def get_opportunity(self, opportunity_id: str):
        """GET /opportunities/{id} - Get single opportunity"""
        return self._request("GET", f"/opportunities/{opportunity_id}")

    def create_opportunity(self, data: dict):
        """POST /opportunities - Create new opportunity
        
        Required fields:
        - pipelineId: Pipeline ID
        - name: Opportunity name
        - contactId: Contact ID
        Optional fields:
        - stageId: Stage ID
        - monetaryValue: Value of opportunity
        - status: Status (open, won, lost, abandoned)
        """
        return self._request("POST", "/opportunities/", data=data)

    def update_opportunity(self, opportunity_id: str, data: dict):
        """PUT /opportunities/{id} - Update opportunity"""
        return self._request("PUT", f"/opportunities/{opportunity_id}", data=data)

    def update_opportunity_status(self, opportunity_id: str, status: str):
        """PUT /opportunities/{id}/status - Update opportunity status
        
        status values: open, won, lost, abandoned
        """
        return self._request("PUT", f"/opportunities/{opportunity_id}/status", data={"status": status})

    def delete_opportunity(self, opportunity_id: str):
        """DELETE /opportunities/{id} - Delete opportunity"""
        return self._request("DELETE", f"/opportunities/{opportunity_id}")

    # ================================
    # Messaging (Email, SMS, WhatsApp)
    # ================================
    def send_message(self, message_type: str, contact_id: str, message: str, **kwargs):
        """POST /conversations/messages - Send message via Email, SMS, or WhatsApp
        
        Args:
            message_type: 'Email', 'SMS', or 'WhatsApp' (or 'TYPE_EMAIL', 'TYPE_SMS', 'TYPE_WHATSAPP')
            contact_id: Contact ID to send message to
            message: Message body/content
            
        Additional kwargs for Email:
            - subject: Email subject
            - html: HTML content (alternative to message)
            - attachments: List of attachment URLs
            
        Additional kwargs for SMS/WhatsApp:
            - attachments: List of attachment URLs
        """
        # Normalize message type
        type_map = {
            'Email': 'Email',
            'SMS': 'SMS',
            'WhatsApp': 'WhatsApp',
            'TYPE_EMAIL': 'Email',
            'TYPE_SMS': 'SMS',
            'TYPE_WHATSAPP': 'WhatsApp',
            'email': 'Email',
            'sms': 'SMS',
            'whatsapp': 'WhatsApp'
        }
        normalized_type = type_map.get(message_type, message_type)
        
        data = {
            "type": normalized_type,
            "contactId": contact_id,
            "message": message
        }
        
        # Add optional fields
        if kwargs.get('subject'):
            data['subject'] = kwargs['subject']
        if kwargs.get('html'):
            data['html'] = kwargs['html']
        if kwargs.get('attachments'):
            data['attachments'] = kwargs['attachments']
        if kwargs.get('conversationId'):
            data['conversationId'] = kwargs['conversationId']
        if kwargs.get('conversationProviderId'):
            data['conversationProviderId'] = kwargs['conversationProviderId']
            
        return self._request("POST", "/conversations/messages", data=data)

    def send_email(self, contact_id: str, subject: str, message: str, html: str = None, attachments: list = None):
        """Send email message to a contact"""
        return self.send_message(
            message_type='Email',
            contact_id=contact_id,
            message=message,
            subject=subject,
            html=html,
            attachments=attachments
        )

    def send_sms(self, contact_id: str, message: str, attachments: list = None):
        """Send SMS message to a contact"""
        return self.send_message(
            message_type='SMS',
            contact_id=contact_id,
            message=message,
            attachments=attachments
        )

    def send_whatsapp(self, contact_id: str, message: str, attachments: list = None):
        """Send WhatsApp message to a contact"""
        return self.send_message(
            message_type='WhatsApp',
            contact_id=contact_id,
            message=message,
            attachments=attachments
        )

    def get_conversation_messages(self, conversation_id: str, **query):
        """GET /conversations/{id}/messages - Get messages for a conversation"""
        return self._request("GET", f"/conversations/{conversation_id}/messages", params=query)

    # ============
    # Contact Tags
    # ============
    def add_tags_to_contact(self, contact_id: str, tags: list):
        """POST /contacts/{id}/tags - Add tags to a contact
        
        Args:
            contact_id: Contact ID
            tags: List of tag names to add
        """
        return self._request("POST", f"/contacts/{contact_id}/tags", data={"tags": tags})

    def remove_tag_from_contact(self, contact_id: str, tag_id: str):
        """DELETE /contacts/{id}/tags/{tagId} - Remove tag from contact"""
        return self._request("DELETE", f"/contacts/{contact_id}/tags")

    # =================
    # Contact Campaigns
    # =================
    def add_contact_to_campaign(self, contact_id: str, campaign_id: str):
        """POST /contacts/{id}/campaigns/{campaignId} - Add contact to campaign"""
        return self._request("POST", f"/contacts/{contact_id}/campaigns/{campaign_id}")

    def remove_contact_from_campaign(self, contact_id: str, campaign_id: str):
        """DELETE /contacts/{id}/campaigns/{campaignId} - Remove contact from campaign"""
        return self._request("DELETE", f"/contacts/{contact_id}/campaigns/{campaign_id}")

    # =================
    # Contact Workflows
    # =================
    def add_contact_to_workflow(self, contact_id: str, workflow_id: str, event_start_time: str = None):
        """POST /contacts/{id}/workflow/{workflowId} - Add contact to workflow
        
        Args:
            contact_id: Contact ID
            workflow_id: Workflow ID
            event_start_time: Optional event start time (ISO format)
        """
        data = {}
        if event_start_time:
            data['eventStartTime'] = event_start_time
        return self._request("POST", f"/contacts/{contact_id}/workflow/{workflow_id}", data=data if data else None)

    def remove_contact_from_workflow(self, contact_id: str, workflow_id: str):
        """DELETE /contacts/{id}/workflow/{workflowId} - Remove contact from workflow"""
        return self._request("DELETE", f"/contacts/{contact_id}/workflow/{workflow_id}")

    # ======================
    # Analytics / Statistics
    # ======================
    def get_opportunity_stats(self, pipeline_id: str = None, **query):
        """Get opportunity statistics aggregated by status
        
        Returns counts for: new, engaged, purchased (won), long-term (lost/abandoned)
        """
        opportunities = self.search_opportunities(pipelineId=pipeline_id, **query)
        
        stats = {
            'total': 0,
            'new_opportunities': 0,
            'engaged_leads': 0,
            'purchased': 0,
            'long_term_future': 0,
            'open': 0,
            'won': 0,
            'lost': 0,
            'abandoned': 0
        }
        
        if 'opportunities' in opportunities:
            opps = opportunities['opportunities']
            stats['total'] = len(opps)
            
            for opp in opps:
                status = opp.get('status', '').lower()
                stats[status] = stats.get(status, 0) + 1
                
            # Map to user-friendly categories
            stats['purchased'] = stats['won']
            stats['long_term_future'] = stats['lost'] + stats['abandoned']
            # New/engaged can be determined by stage or other criteria
            stats['open'] = stats.get('open', 0)
            stats['new_opportunities'] = stats['total'] - stats['won'] - stats['lost'] - stats['abandoned']
            
        return stats

    def get_dashboard_stats(self, **query):
        """Get comprehensive dashboard statistics
        
        Aggregates data from opportunities, contacts, and tasks
        """
        stats = {
            'opportunities': self.get_opportunity_stats(**query),
            'pipelines': [],
            'recent_activity': []
        }
        
        # Get pipeline summaries
        try:
            pipelines = self.list_pipelines()
            if 'pipelines' in pipelines:
                stats['pipelines'] = [
                    {
                        'id': p.get('id'),
                        'name': p.get('name'),
                        'stages_count': len(p.get('stages', []))
                    }
                    for p in pipelines['pipelines']
                ]
        except Exception:
            pass
            
        return stats