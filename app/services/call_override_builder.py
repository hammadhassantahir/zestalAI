import json
from .language_service import resolve_language, resolve_voice
from .call_script_templates import get_template


def build_overrides(user_config, customer_number, lead_context=None):
    overrides = {}

    lang = resolve_language(customer_number, user_config)

    voice_provider, voice_id = resolve_voice(customer_number, user_config)
    overrides['voice'] = {
        'provider': voice_provider,
        'voiceId': voice_id,
    }

    # Build system prompt
    template = get_template(user_config.active_template)
    base_prompt = template['system_prompt'] if template else ''
    prompt_parts = [base_prompt]

    # Tone
    if user_config.tone == 'informal':
        prompt_parts.append("\nTone: Be casual, friendly, and conversational. Use informal language.")
    else:
        prompt_parts.append("\nTone: Be professional and polite. Use formal language.")

    # Language
    prompt_parts.append(f"\nLanguage: Speak in {lang}.")
    prompt_parts.append(
        f"Fallback: If the lead responds in a different language, "
        f"try to switch. If you can't, continue in {user_config.fallback_language or 'en-US'}."
    )

    # Brand prompt
    if user_config.system_prompt_base:
        prompt_parts.append(f"\nBrand context:\n{user_config.system_prompt_base}")

    # Lead context
    if lead_context:
        ctx_str = json.dumps(lead_context) if isinstance(lead_context, dict) else str(lead_context)
        prompt_parts.append(f"\nLead context (use this to personalize):\n{ctx_str}")

    overrides['model'] = {
        'messages': [{'role': 'system', 'content': '\n'.join(prompt_parts)}]
    }

    # Greeting
    if user_config.greeting_template:
        first_msg = user_config.greeting_template
        if lead_context and isinstance(lead_context, dict):
            for key, val in lead_context.items():
                first_msg = first_msg.replace(f'{{{key}}}', str(val))
        overrides['firstMessage'] = first_msg
    elif template and template.get('first_message'):
        overrides['firstMessage'] = template['first_message']

    # Analysis plan from template
    if template:
        overrides['analysisPlan'] = {
            'structuredDataSchema': template['structured_data_schema'],
            'structuredDataPrompt': template['structured_data_prompt'],
        }

    return overrides
