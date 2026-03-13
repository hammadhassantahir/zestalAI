"""
Hardcoded call script templates.
Each template defines a system prompt, first message, and structured data extraction schema.
"""

TEMPLATES = {
    "lead_qualification": {
        "name": "Lead Qualification",
        "description": "Qualify leads by collecting budget, timeline, decision-maker status, and pain points",
        "first_message": "Hi there! Thanks for taking my call. I'd love to learn a bit about your business needs so we can see how we might help. Do you have a couple of minutes?",
        "system_prompt": (
            "You are a professional lead qualification agent. Your goal is to have a natural, "
            "friendly conversation while gathering key qualification information.\n\n"
            "Follow this conversation flow:\n"
            "1. Greet the contact and confirm they have time to talk\n"
            "2. Ask for their full name and company if not already known\n"
            "3. Ask about their main business challenges or pain points\n"
            "4. Ask about their budget range for a solution\n"
            "5. Ask about their timeline — when do they need a solution\n"
            "6. Ask if they are the decision maker or who else is involved\n"
            "7. Thank them and let them know someone will follow up\n\n"
            "Rules:\n"
            "- Keep the conversation natural and conversational, not robotic\n"
            "- If they seem rushed, prioritize the most important questions\n"
            "- Don't push if they decline to answer a question\n"
            "- Keep responses brief (1-2 sentences)\n"
            "- Be warm and professional throughout"
        ),
        "structured_data_schema": {
            "type": "object",
            "properties": {
                "full_name": {"type": "string", "description": "The contact's full name"},
                "company": {"type": "string", "description": "The contact's company or business name"},
                "budget_range": {"type": "string", "description": "Their budget range or bracket"},
                "timeline": {"type": "string", "description": "When they need the solution"},
                "decision_maker": {"type": "boolean", "description": "Whether they are the decision maker"},
                "pain_points": {"type": "string", "description": "Their main business challenges"},
                "interest_level": {
                    "type": "string",
                    "enum": ["hot", "warm", "cold"],
                    "description": "Overall interest level based on the conversation"
                },
            },
        },
        "structured_data_prompt": (
            "Extract the following fields from the call transcript. "
            "For interest_level, infer from the overall tone: "
            "'hot' if very interested and ready to act, "
            "'warm' if interested but not urgent, "
            "'cold' if not interested or disengaged."
        ),
    },
    "appointment_booking": {
        "name": "Appointment Booking",
        "description": "Book appointments by collecting contact details, preferred date/time, and reason for visit",
        "first_message": "Hello! I'm calling to help you schedule an appointment. Is now a good time to set that up?",
        "system_prompt": (
            "You are a professional appointment booking agent. Your goal is to schedule an "
            "appointment by collecting the necessary details.\n\n"
            "Follow this conversation flow:\n"
            "1. Confirm the contact is available to talk\n"
            "2. Ask for their full name\n"
            "3. Confirm their phone number and ask for email\n"
            "4. Ask what the appointment is for (reason for visit)\n"
            "5. Ask for their preferred date and time\n"
            "6. Confirm the appointment details back to them\n"
            "7. Thank them and let them know they'll receive a confirmation\n\n"
            "Rules:\n"
            "- Keep the conversation natural and efficient\n"
            "- If they give partial info, ask follow-up questions\n"
            "- Repeat back the appointment details for confirmation\n"
            "- Keep responses brief (1-2 sentences)\n"
            "- Be friendly and professional"
        ),
        "structured_data_schema": {
            "type": "object",
            "properties": {
                "full_name": {"type": "string", "description": "The contact's full name"},
                "phone_number": {"type": "string", "description": "Their phone number"},
                "email": {"type": "string", "description": "Their email address"},
                "preferred_date": {"type": "string", "description": "Preferred appointment date"},
                "preferred_time": {"type": "string", "description": "Preferred appointment time"},
                "reason_for_visit": {"type": "string", "description": "Why they need the appointment"},
                "confirmed": {
                    "type": "boolean",
                    "description": "Whether the contact confirmed the appointment"
                },
            },
        },
        "structured_data_prompt": (
            "Extract the following fields from the call transcript. "
            "For confirmed, set to true only if the contact explicitly agreed to the appointment details."
        ),
    },
}


def get_template(template_name):
    """Get a template by name. Returns None if not found."""
    return TEMPLATES.get(template_name)


def list_templates():
    """Return summary of all available templates."""
    return [
        {
            "name": key,
            "display_name": tmpl["name"],
            "description": tmpl["description"],
            "fields": list(tmpl["structured_data_schema"]["properties"].keys()),
        }
        for key, tmpl in TEMPLATES.items()
    ]
