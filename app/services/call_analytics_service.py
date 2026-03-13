import json
import logging
from flask import current_app
from ..extensions import db
from ..models.call_analytics import CallAnalytics
from ..models.call_log import CallLog

logger = logging.getLogger(__name__)

ANALYSIS_PROMPT = """Analyze this call transcript and extract:

1. sentiment: "positive", "negative", or "neutral"
2. interest_level: 1-10 (10 = very interested)
3. objections: list of objection categories from: ["price", "timing", "competitor", "not_interested", "need_approval", "no_budget", "other"]
4. success_evaluation: "yes" (call goal achieved), "no" (not achieved), or "partial"

Transcript:
{transcript}

Call summary:
{summary}

Respond in JSON only:
{{"sentiment": "...", "interest_level": N, "objections": [...], "success_evaluation": "..."}}"""


def analyze_call(call_log_id):
    call = CallLog.query.get(call_log_id)
    if not call or not call.transcript:
        logger.warning(f"No transcript for call {call_log_id}, skipping analysis")
        return None

    existing = CallAnalytics.query.filter_by(call_log_id=call_log_id).first()
    if existing:
        return existing

    try:
        import openai
        client = openai.OpenAI(api_key=current_app.config.get('OPENAI_API_KEY'))

        prompt = ANALYSIS_PROMPT.format(
            transcript=call.transcript[:4000],
            summary=call.summary or 'No summary available',
        )

        resp = client.chat.completions.create(
            model='gpt-4o-mini',
            messages=[{'role': 'user', 'content': prompt}],
            response_format={'type': 'json_object'},
            temperature=0.3,
        )

        result = json.loads(resp.choices[0].message.content)

        analytics = CallAnalytics(
            call_log_id=call.id,
            user_id=call.user_id,
            sentiment=result.get('sentiment'),
            interest_level=result.get('interest_level'),
            objections=json.dumps(result.get('objections', [])),
            success_evaluation=result.get('success_evaluation'),
            extraction_status=CallAnalytics.STATUS_COMPLETED,
        )

        # Store Vapi structured data if available
        if call.structured_data:
            try:
                structured = json.loads(call.structured_data)
                analytics.extracted_data = json.dumps(structured.get('structuredData', {}))
                analytics.template_name = call.template_used
            except (json.JSONDecodeError, TypeError):
                pass

        db.session.add(analytics)
        db.session.commit()
        logger.info(f"Call analytics created for call {call_log_id}")
        return analytics

    except Exception as e:
        logger.error(f"Call analysis failed for {call_log_id}: {str(e)}")
        analytics = CallAnalytics(
            call_log_id=call.id,
            user_id=call.user_id,
            extraction_status=CallAnalytics.STATUS_FAILED,
        )
        db.session.add(analytics)
        db.session.commit()
        return analytics
