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
