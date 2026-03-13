import phonenumbers
from phonenumbers import geocoder, timezone as pn_timezone


# country_code (2-letter ISO) -> language/voice defaults
LANGUAGE_MAP = {
    'US': {'lang': 'en-US', 'voice_provider': 'openai', 'voice_id': 'alloy'},
    'GB': {'lang': 'en-GB', 'voice_provider': 'openai', 'voice_id': 'alloy'},
    'AU': {'lang': 'en-AU', 'voice_provider': 'openai', 'voice_id': 'alloy'},
    'DK': {'lang': 'da-DK', 'voice_provider': 'openai', 'voice_id': 'alloy'},
    'DE': {'lang': 'de-DE', 'voice_provider': 'openai', 'voice_id': 'alloy'},
    'FR': {'lang': 'fr-FR', 'voice_provider': 'openai', 'voice_id': 'alloy'},
    'ES': {'lang': 'es-ES', 'voice_provider': 'openai', 'voice_id': 'alloy'},
    'IT': {'lang': 'it-IT', 'voice_provider': 'openai', 'voice_id': 'alloy'},
    'NL': {'lang': 'nl-NL', 'voice_provider': 'openai', 'voice_id': 'alloy'},
    'SE': {'lang': 'sv-SE', 'voice_provider': 'openai', 'voice_id': 'alloy'},
    'NO': {'lang': 'nb-NO', 'voice_provider': 'openai', 'voice_id': 'alloy'},
    'PT': {'lang': 'pt-PT', 'voice_provider': 'openai', 'voice_id': 'alloy'},
    'BR': {'lang': 'pt-BR', 'voice_provider': 'openai', 'voice_id': 'alloy'},
    'JP': {'lang': 'ja-JP', 'voice_provider': 'openai', 'voice_id': 'alloy'},
    'KR': {'lang': 'ko-KR', 'voice_provider': 'openai', 'voice_id': 'alloy'},
    'IN': {'lang': 'hi-IN', 'voice_provider': 'openai', 'voice_id': 'alloy'},
}

SUPPORTED_LANGUAGES = [
    {'code': 'en-US', 'name': 'English (US)'},
    {'code': 'en-GB', 'name': 'English (UK)'},
    {'code': 'da-DK', 'name': 'Danish'},
    {'code': 'de-DE', 'name': 'German'},
    {'code': 'fr-FR', 'name': 'French'},
    {'code': 'es-ES', 'name': 'Spanish'},
    {'code': 'it-IT', 'name': 'Italian'},
    {'code': 'nl-NL', 'name': 'Dutch'},
    {'code': 'sv-SE', 'name': 'Swedish'},
    {'code': 'nb-NO', 'name': 'Norwegian'},
    {'code': 'pt-PT', 'name': 'Portuguese'},
    {'code': 'pt-BR', 'name': 'Portuguese (Brazil)'},
    {'code': 'ja-JP', 'name': 'Japanese'},
    {'code': 'ko-KR', 'name': 'Korean'},
    {'code': 'hi-IN', 'name': 'Hindi'},
]


def parse_number(phone_number_str):
    """Parse once, reuse everywhere."""
    try:
        return phonenumbers.parse(phone_number_str, None)
    except Exception:
        return None


def get_country_from_number(phone_number_str):
    parsed = parse_number(phone_number_str)
    if not parsed:
        return None, None
    return geocoder.country_name_for_number(parsed, 'en'), \
           phonenumbers.region_code_for_number(parsed)


def get_timezone_from_number(phone_number_str):
    parsed = parse_number(phone_number_str)
    if not parsed:
        return None
    tzs = pn_timezone.time_zones_for_number(parsed)
    return list(tzs)[0] if tzs else None


def get_country_and_timezone(phone_number_str):
    """Parse number once, return (country_name, region_code, timezone)."""
    parsed = parse_number(phone_number_str)
    if not parsed:
        return None, None, None
    country_name = geocoder.country_name_for_number(parsed, 'en')
    region_code = phonenumbers.region_code_for_number(parsed)
    tzs = pn_timezone.time_zones_for_number(parsed)
    tz = list(tzs)[0] if tzs else None
    return country_name, region_code, tz


def resolve_language(customer_number, user_config, country_code=None):
    """Waterfall: user override -> country default -> user fallback -> en-US"""
    import json
    if country_code is None:
        _, country_code = get_country_from_number(customer_number)

    # 1. user override for this country
    if country_code and user_config.language_overrides:
        try:
            overrides = json.loads(user_config.language_overrides) if isinstance(
                user_config.language_overrides, str) else user_config.language_overrides
            if country_code in overrides:
                return overrides[country_code]
        except (json.JSONDecodeError, TypeError):
            pass

    # 2. default map
    if country_code and country_code in LANGUAGE_MAP:
        return LANGUAGE_MAP[country_code]['lang']

    # 3. user fallback
    if user_config.fallback_language:
        return user_config.fallback_language

    # 4. system default
    return 'en-US'


def resolve_voice(customer_number, user_config, country_code=None):
    if country_code is None:
        _, country_code = get_country_from_number(customer_number)

    if user_config.voice_provider and user_config.voice_id:
        return user_config.voice_provider, user_config.voice_id

    if country_code and country_code in LANGUAGE_MAP:
        entry = LANGUAGE_MAP[country_code]
        return entry['voice_provider'], entry['voice_id']

    return 'openai', 'alloy'


def is_in_call_window(customer_number, user_config, tz_str=None):
    from datetime import datetime
    import pytz
    import json

    if not user_config.call_window_start or not user_config.call_window_end:
        return True

    if tz_str is None:
        tz_str = get_timezone_from_number(customer_number)
    if not tz_str:
        tz_str = user_config.call_window_timezone or 'UTC'

    try:
        tz = pytz.timezone(tz_str)
    except pytz.exceptions.UnknownTimeZoneError:
        tz = pytz.UTC

    now_local = datetime.now(tz)

    if user_config.call_window_days:
        days = json.loads(user_config.call_window_days) if isinstance(
            user_config.call_window_days, str) else user_config.call_window_days
        if now_local.isoweekday() not in days:
            return False

    current_time = now_local.time()
    return user_config.call_window_start <= current_time <= user_config.call_window_end


def get_next_call_window(customer_number, user_config, tz_str=None):
    """Return next valid datetime (UTC) when the call window opens. None if no window set."""
    from datetime import datetime, timedelta
    import pytz
    import json

    if not user_config.call_window_start or not user_config.call_window_end:
        return None

    if tz_str is None:
        tz_str = get_timezone_from_number(customer_number)
    if not tz_str:
        tz_str = user_config.call_window_timezone or 'UTC'

    try:
        tz = pytz.timezone(tz_str)
    except pytz.exceptions.UnknownTimeZoneError:
        tz = pytz.UTC

    now_local = datetime.now(tz)

    allowed_days = None
    if user_config.call_window_days:
        allowed_days = json.loads(user_config.call_window_days) if isinstance(
            user_config.call_window_days, str) else user_config.call_window_days

    # try today first, then next 7 days
    for offset in range(8):
        candidate = now_local + timedelta(days=offset)

        if allowed_days and candidate.isoweekday() not in allowed_days:
            continue

        # if today and still before window end, use window start (or now if past start)
        if offset == 0 and candidate.time() < user_config.call_window_end:
            if candidate.time() >= user_config.call_window_start:
                return None  # already in window, no scheduling needed
            target = candidate.replace(
                hour=user_config.call_window_start.hour,
                minute=user_config.call_window_start.minute,
                second=0, microsecond=0,
            )
            return target.astimezone(pytz.UTC).replace(tzinfo=None)

        # future day — use window start
        if offset > 0:
            target = candidate.replace(
                hour=user_config.call_window_start.hour,
                minute=user_config.call_window_start.minute,
                second=0, microsecond=0,
            )
            return target.astimezone(pytz.UTC).replace(tzinfo=None)

    return None
