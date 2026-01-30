from flask import Blueprint, current_app, request, jsonify
from app.script.highLevelAPI import LeadConnectorClient
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps
import logging

ghl = Blueprint('ghl', __name__)

def init_ghl_client():
    """Initialize GHL client with configuration"""
    return LeadConnectorClient(
        access_token=current_app.config['GHL_ACCESS_TOKEN'],
        location_id=current_app.config['GHL_LOCATION_ID']
    )

# ========== Contact Management ==========
@ghl.route('/contacts', methods=['GET'])
@jwt_required()
def list_contacts():
    print('THEREEEEEEEEEEEEEEEEEEEEE')
    """List contacts with optional filters"""
    try:
        client = init_ghl_client()
        query_params = {
            'limit': request.args.get('limit', type=int),
            'page': request.args.get('page', type=int),
            'query': request.args.get('query'),
            'sortBy': request.args.get('sortBy'),
            'tags': request.args.get('tags'),
            'dateCreated': request.args.get('dateCreated')
        }
        # Remove None values
        query_params = {k: v for k, v in query_params.items() if v is not None}
        print(query_params)
        contacts = client.list_contacts(**query_params)
        return jsonify(contacts), 200
    except Exception as e:
        logging.error(f"Error listing contacts: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/contacts/<contact_id>', methods=['GET'])
@jwt_required()
def get_contact(contact_id):
    """Get a specific contact by ID"""
    try:
        client = init_ghl_client()
        contact = client.get_contact(contact_id)
        return jsonify(contact), 200
    except Exception as e:
        logging.error(f"Error getting contact {contact_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/contacts', methods=['POST'])
@jwt_required()
def create_contact():
    """Create a new contact"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        client = init_ghl_client()
        contact = client.create_contact(data)
        return jsonify(contact), 201
    except Exception as e:
        logging.error(f"Error creating contact: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/contacts/<contact_id>', methods=['PUT'])
@jwt_required()
def update_contact(contact_id):
    """Update an existing contact"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        client = init_ghl_client()
        contact = client.update_contact(contact_id, data)
        return jsonify(contact), 200
    except Exception as e:
        logging.error(f"Error updating contact {contact_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/contacts/<contact_id>', methods=['DELETE'])
@jwt_required()
def delete_contact(contact_id):
    """Delete a contact"""
    try:
        client = init_ghl_client()
        client.delete_contact(contact_id)
        return jsonify({"message": "Contact deleted successfully"}), 200
    except Exception as e:
        logging.error(f"Error deleting contact {contact_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ========== Location Management ==========
@ghl.route('/locations/<location_id>', methods=['GET'])
@jwt_required()
def get_location(location_id):
    """Get location details"""
    try:
        client = init_ghl_client()
        location = client.get_location(location_id)
        return jsonify(location), 200
    except Exception as e:
        logging.error(f"Error getting location {location_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ========== Campaign Management ==========
@ghl.route('/campaigns', methods=['GET'])
@jwt_required()
def list_campaigns():
    """List campaigns with optional filters"""
    try:
        client = init_ghl_client()
        query_params = {
            'limit': request.args.get('limit', type=int),
            'page': request.args.get('page', type=int),
            'status': request.args.get('status')
        }
        query_params = {k: v for k, v in query_params.items() if v is not None}
        campaigns = client.list_campaigns(**query_params)
        return jsonify(campaigns), 200
    except Exception as e:
        logging.error(f"Error listing campaigns: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ========== Task Management ==========
@ghl.route('/tasks', methods=['GET'])
@jwt_required()
def list_tasks():
    """List tasks with optional filters"""
    try:
        client = init_ghl_client()
        query_params = {
            'limit': request.args.get('limit', type=int),
            'page': request.args.get('page', type=int),
            'status': request.args.get('status'),
            'dueDate': request.args.get('dueDate')
        }
        query_params = {k: v for k, v in query_params.items() if v is not None}
        tasks = client.list_tasks(**query_params)
        return jsonify(tasks), 200
    except Exception as e:
        logging.error(f"Error listing tasks: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/tasks', methods=['POST'])
@jwt_required()
def create_task():
    """Create a new task"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        client = init_ghl_client()
        task = client.create_task(data)
        return jsonify(task), 201
    except Exception as e:
        logging.error(f"Error creating task: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/tasks/<task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """Update an existing task"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        client = init_ghl_client()
        task = client.update_task(task_id, data)
        return jsonify(task), 200
    except Exception as e:
        logging.error(f"Error updating task {task_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/tasks/<task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    """Delete a task"""
    try:
        client = init_ghl_client()
        client.delete_task(task_id)
        return jsonify({"message": "Task deleted successfully"}), 200
    except Exception as e:
        logging.error(f"Error deleting task {task_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ========== Calendar Management ==========
@ghl.route('/calendars', methods=['GET'])
@jwt_required()
def list_calendars():
    """List calendars"""
    try:
        client = init_ghl_client()
        query_params = {
            'limit': request.args.get('limit', type=int),
            'page': request.args.get('page', type=int)
        }
        query_params = {k: v for k, v in query_params.items() if v is not None}
        calendars = client.list_calendars(**query_params)
        return jsonify(calendars), 200
    except Exception as e:
        logging.error(f"Error listing calendars: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/calendars/<calendar_id>', methods=['GET'])
@jwt_required()
def get_calendar(calendar_id):
    """Get a specific calendar"""
    try:
        client = init_ghl_client()
        calendar = client.get_calendar(calendar_id)
        return jsonify(calendar), 200
    except Exception as e:
        logging.error(f"Error getting calendar {calendar_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/calendars', methods=['POST'])
@jwt_required()
def create_calendar():
    """Create a new calendar"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        client = init_ghl_client()
        calendar = client.create_calendar(data)
        return jsonify(calendar), 201
    except Exception as e:
        logging.error(f"Error creating calendar: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/calendars/<calendar_id>', methods=['PUT'])
@jwt_required()
def update_calendar(calendar_id):
    """Update an existing calendar"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        client = init_ghl_client()
        calendar = client.update_calendar(calendar_id, data)
        return jsonify(calendar), 200
    except Exception as e:
        logging.error(f"Error updating calendar {calendar_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/calendars/<calendar_id>', methods=['DELETE'])
@jwt_required()
def delete_calendar(calendar_id):
    """Delete a calendar"""
    try:
        client = init_ghl_client()
        client.delete_calendar(calendar_id)
        return jsonify({"message": "Calendar deleted successfully"}), 200
    except Exception as e:
        logging.error(f"Error deleting calendar {calendar_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ========== Pipeline Management ==========
@ghl.route('/pipelines', methods=['GET'])
@jwt_required()
def list_pipelines():
    """List all pipelines"""
    try:
        client = init_ghl_client()
        pipelines = client.list_pipelines()
        return jsonify(pipelines), 200
    except Exception as e:
        logging.error(f"Error listing pipelines: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/pipelines/<pipeline_id>/stages', methods=['GET'])
@jwt_required()
def get_pipeline_stages(pipeline_id):
    """Get stages for a specific pipeline"""
    try:
        client = init_ghl_client()
        stages = client.get_pipeline_stages(pipeline_id)
        return jsonify(stages), 200
    except Exception as e:
        logging.error(f"Error getting pipeline stages {pipeline_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ========== Opportunity Management ==========
@ghl.route('/opportunities', methods=['GET'])
@jwt_required()
def search_opportunities():
    """Search/filter opportunities"""
    try:
        client = init_ghl_client()
        query_params = {
            'limit': request.args.get('limit', type=int),
            'page': request.args.get('page', type=int),
            'pipelineId': request.args.get('pipelineId'),
            'stageId': request.args.get('stageId'),
            'status': request.args.get('status'),
            'contactId': request.args.get('contactId'),
            'startDate': request.args.get('startDate'),
            'endDate': request.args.get('endDate'),
            'q': request.args.get('q')
        }
        query_params = {k: v for k, v in query_params.items() if v is not None}
        opportunities = client.search_opportunities(**query_params)
        return jsonify(opportunities), 200
    except Exception as e:
        logging.error(f"Error searching opportunities: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/opportunities/<opportunity_id>', methods=['GET'])
@jwt_required()
def get_opportunity(opportunity_id):
    """Get a specific opportunity by ID"""
    try:
        client = init_ghl_client()
        opportunity = client.get_opportunity(opportunity_id)
        return jsonify(opportunity), 200
    except Exception as e:
        logging.error(f"Error getting opportunity {opportunity_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/opportunities', methods=['POST'])
@jwt_required()
def create_opportunity():
    """Create a new opportunity"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Validate required fields
        required_fields = ['pipelineId', 'name', 'contactId']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        client = init_ghl_client()
        opportunity = client.create_opportunity(data)
        return jsonify(opportunity), 201
    except Exception as e:
        logging.error(f"Error creating opportunity: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/opportunities/<opportunity_id>', methods=['PUT'])
@jwt_required()
def update_opportunity(opportunity_id):
    """Update an existing opportunity"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        client = init_ghl_client()
        opportunity = client.update_opportunity(opportunity_id, data)
        return jsonify(opportunity), 200
    except Exception as e:
        logging.error(f"Error updating opportunity {opportunity_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/opportunities/<opportunity_id>/status', methods=['PUT'])
@jwt_required()
def update_opportunity_status(opportunity_id):
    """Update opportunity status"""
    try:
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({"error": "Status is required"}), 400
        
        client = init_ghl_client()
        opportunity = client.update_opportunity_status(opportunity_id, data['status'])
        return jsonify(opportunity), 200
    except Exception as e:
        logging.error(f"Error updating opportunity status {opportunity_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/opportunities/<opportunity_id>', methods=['DELETE'])
@jwt_required()
def delete_opportunity(opportunity_id):
    """Delete an opportunity"""
    try:
        client = init_ghl_client()
        client.delete_opportunity(opportunity_id)
        return jsonify({"message": "Opportunity deleted successfully"}), 200
    except Exception as e:
        logging.error(f"Error deleting opportunity {opportunity_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ========== Messaging (Email, SMS, WhatsApp) ==========
@ghl.route('/messages/email', methods=['POST'])
@jwt_required()
def send_email():
    """Send email message to a contact"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        required_fields = ['contactId', 'subject', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        client = init_ghl_client()
        result = client.send_email(
            contact_id=data['contactId'],
            subject=data['subject'],
            message=data['message'],
            html=data.get('html'),
            attachments=data.get('attachments')
        )
        return jsonify(result), 200
    except Exception as e:
        logging.error(f"Error sending email: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/messages/sms', methods=['POST'])
@jwt_required()
def send_sms():
    """Send SMS message to a contact"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        required_fields = ['contactId', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        client = init_ghl_client()
        result = client.send_sms(
            contact_id=data['contactId'],
            message=data['message'],
            attachments=data.get('attachments')
        )
        return jsonify(result), 200
    except Exception as e:
        logging.error(f"Error sending SMS: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/messages/whatsapp', methods=['POST'])
@jwt_required()
def send_whatsapp():
    """Send WhatsApp message to a contact"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        required_fields = ['contactId', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        client = init_ghl_client()
        result = client.send_whatsapp(
            contact_id=data['contactId'],
            message=data['message'],
            attachments=data.get('attachments')
        )
        return jsonify(result), 200
    except Exception as e:
        logging.error(f"Error sending WhatsApp: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/conversations/<conversation_id>/messages', methods=['GET'])
@jwt_required()
def get_conversation_messages(conversation_id):
    """Get messages for a conversation"""
    try:
        client = init_ghl_client()
        query_params = {
            'limit': request.args.get('limit', type=int),
            'lastMessageId': request.args.get('lastMessageId')
        }
        query_params = {k: v for k, v in query_params.items() if v is not None}
        messages = client.get_conversation_messages(conversation_id, **query_params)
        return jsonify(messages), 200
    except Exception as e:
        logging.error(f"Error getting conversation messages {conversation_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ========== Tag Management ==========
@ghl.route('/tags', methods=['GET'])
@jwt_required()
def list_tags():
    """List all tags"""
    try:
        client = init_ghl_client()
        query_params = {
            'limit': request.args.get('limit', type=int),
            'page': request.args.get('page', type=int)
        }
        query_params = {k: v for k, v in query_params.items() if v is not None}
        tags = client.list_tags(**query_params)
        return jsonify(tags), 200
    except Exception as e:
        logging.error(f"Error listing tags: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/tags', methods=['POST'])
@jwt_required()
def create_tag():
    """Create a new tag"""
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({"error": "Tag name is required"}), 400
        
        client = init_ghl_client()
        tag = client.create_tag(data)
        return jsonify(tag), 201
    except Exception as e:
        logging.error(f"Error creating tag: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/tags/<tag_id>', methods=['DELETE'])
@jwt_required()
def delete_tag(tag_id):
    """Delete a tag"""
    try:
        client = init_ghl_client()
        client.delete_tag(tag_id)
        return jsonify({"message": "Tag deleted successfully"}), 200
    except Exception as e:
        logging.error(f"Error deleting tag {tag_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/contacts/<contact_id>/tags', methods=['POST'])
@jwt_required()
def add_tags_to_contact(contact_id):
    """Add tags to a contact"""
    try:
        data = request.get_json()
        if not data or 'tags' not in data:
            return jsonify({"error": "Tags array is required"}), 400
        
        client = init_ghl_client()
        result = client.add_tags_to_contact(contact_id, data['tags'])
        return jsonify(result), 200
    except Exception as e:
        logging.error(f"Error adding tags to contact {contact_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/contacts/<contact_id>/tags/<tag_id>', methods=['DELETE'])
@jwt_required()
def remove_tag_from_contact(contact_id, tag_id):
    """Remove tag from a contact"""
    try:
        client = init_ghl_client()
        result = client.remove_tag_from_contact(contact_id, tag_id)
        return jsonify({"message": "Tag removed from contact successfully"}), 200
    except Exception as e:
        logging.error(f"Error removing tag from contact {contact_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ========== Contact Campaign Management ==========
@ghl.route('/contacts/<contact_id>/campaigns/<campaign_id>', methods=['POST'])
@jwt_required()
def add_contact_to_campaign(contact_id, campaign_id):
    """Add contact to a campaign"""
    try:
        client = init_ghl_client()
        result = client.add_contact_to_campaign(contact_id, campaign_id)
        return jsonify(result), 200
    except Exception as e:
        logging.error(f"Error adding contact {contact_id} to campaign {campaign_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/contacts/<contact_id>/campaigns/<campaign_id>', methods=['DELETE'])
@jwt_required()
def remove_contact_from_campaign(contact_id, campaign_id):
    """Remove contact from a campaign"""
    try:
        client = init_ghl_client()
        result = client.remove_contact_from_campaign(contact_id, campaign_id)
        return jsonify({"message": "Contact removed from campaign successfully"}), 200
    except Exception as e:
        logging.error(f"Error removing contact {contact_id} from campaign {campaign_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ========== Contact Workflow Management ==========
@ghl.route('/contacts/<contact_id>/workflows/<workflow_id>', methods=['POST'])
@jwt_required()
def add_contact_to_workflow(contact_id, workflow_id):
    """Add contact to a workflow"""
    try:
        data = request.get_json() or {}
        client = init_ghl_client()
        result = client.add_contact_to_workflow(
            contact_id, 
            workflow_id, 
            event_start_time=data.get('eventStartTime')
        )
        return jsonify(result), 200
    except Exception as e:
        logging.error(f"Error adding contact {contact_id} to workflow {workflow_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/contacts/<contact_id>/workflows/<workflow_id>', methods=['DELETE'])
@jwt_required()
def remove_contact_from_workflow(contact_id, workflow_id):
    """Remove contact from a workflow"""
    try:
        client = init_ghl_client()
        result = client.remove_contact_from_workflow(contact_id, workflow_id)
        return jsonify({"message": "Contact removed from workflow successfully"}), 200
    except Exception as e:
        logging.error(f"Error removing contact {contact_id} from workflow {workflow_id}: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ========== Workflow Management ==========
@ghl.route('/workflows', methods=['GET'])
@jwt_required()
def list_workflows():
    """List all workflows"""
    try:
        client = init_ghl_client()
        query_params = {
            'limit': request.args.get('limit', type=int),
            'page': request.args.get('page', type=int)
        }
        query_params = {k: v for k, v in query_params.items() if v is not None}
        workflows = client.list_workflows(**query_params)
        return jsonify(workflows), 200
    except Exception as e:
        logging.error(f"Error listing workflows: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ========== Analytics / Statistics ==========
@ghl.route('/stats/opportunities', methods=['GET'])
@jwt_required()
def get_opportunity_stats():
    """Get opportunity statistics (new, engaged, purchased, long-term)"""
    try:
        client = init_ghl_client()
        query_params = {
            'pipelineId': request.args.get('pipelineId'),
            'startDate': request.args.get('startDate'),
            'endDate': request.args.get('endDate')
        }
        query_params = {k: v for k, v in query_params.items() if v is not None}
        stats = client.get_opportunity_stats(**query_params)
        return jsonify(stats), 200
    except Exception as e:
        logging.error(f"Error getting opportunity stats: {str(e)}")
        return jsonify({"error": str(e)}), 500

@ghl.route('/stats/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get comprehensive dashboard analytics"""
    try:
        client = init_ghl_client()
        query_params = {
            'pipelineId': request.args.get('pipelineId'),
            'startDate': request.args.get('startDate'),
            'endDate': request.args.get('endDate')
        }
        query_params = {k: v for k, v in query_params.items() if v is not None}
        stats = client.get_dashboard_stats(**query_params)
        return jsonify(stats), 200
    except Exception as e:
        logging.error(f"Error getting dashboard stats: {str(e)}")
        return jsonify({"error": str(e)}), 500

