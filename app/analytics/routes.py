from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, case
from ..extensions import db
from ..models.call_log import CallLog
from ..models.call_analytics import CallAnalytics

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/calls/summary', methods=['GET'])
@jwt_required()
def calls_summary():
    user_id = get_jwt_identity()

    # single query for call_logs stats
    call_stats = db.session.query(
        func.count(CallLog.id),
        func.count(case((CallLog.status == CallLog.STATUS_ENDED, 1))),
        func.count(case((CallLog.status == CallLog.STATUS_FAILED, 1))),
        func.avg(case((CallLog.duration_seconds.isnot(None), CallLog.duration_seconds))),
        func.sum(case((CallLog.cost.isnot(None), CallLog.cost))),
    ).filter(CallLog.user_id == user_id).first()

    total, completed, failed = call_stats[0], call_stats[1], call_stats[2]
    avg_duration = call_stats[3] or 0
    total_cost = call_stats[4] or 0

    # single query for analytics stats
    analytics_stats = db.session.query(
        func.avg(case((CallAnalytics.interest_level.isnot(None), CallAnalytics.interest_level))),
        func.count(case((CallAnalytics.success_evaluation == CallAnalytics.SUCCESS_YES, 1))),
    ).filter(CallAnalytics.user_id == user_id).first()

    avg_interest = analytics_stats[0] or 0
    success_count = analytics_stats[1]

    return jsonify({'summary': {
        'total_calls': total, 'completed': completed, 'failed': failed,
        'success_rate': round(success_count / completed * 100, 1) if completed > 0 else 0,
        'avg_duration_seconds': round(float(avg_duration), 1),
        'total_cost': round(float(total_cost), 2),
        'avg_interest_level': round(float(avg_interest), 1),
    }}), 200


@analytics_bp.route('/calls/sentiment', methods=['GET'])
@jwt_required()
def calls_sentiment():
    user_id = get_jwt_identity()
    rows = db.session.query(
        CallAnalytics.sentiment, func.count(CallAnalytics.id)
    ).filter(
        CallAnalytics.user_id == user_id,
        CallAnalytics.sentiment.isnot(None),
    ).group_by(CallAnalytics.sentiment).all()

    counts = {row[0]: row[1] for row in rows}
    return jsonify({'sentiment': {
        'positive': counts.get(CallAnalytics.SENTIMENT_POSITIVE, 0),
        'negative': counts.get(CallAnalytics.SENTIMENT_NEGATIVE, 0),
        'neutral': counts.get(CallAnalytics.SENTIMENT_NEUTRAL, 0),
    }}), 200


@analytics_bp.route('/calls/timeline', methods=['GET'])
@jwt_required()
def calls_timeline():
    user_id = get_jwt_identity()
    days = request.args.get('days', 30, type=int)
    since = datetime.utcnow() - timedelta(days=days)

    rows = db.session.query(
        func.date(CallLog.created_at).label('date'),
        func.count(CallLog.id).label('count'),
    ).filter(
        CallLog.user_id == user_id,
        CallLog.created_at >= since,
    ).group_by(func.date(CallLog.created_at)).order_by(func.date(CallLog.created_at)).all()

    timeline = [{'date': str(row.date), 'count': row.count} for row in rows]
    return jsonify({'timeline': timeline}), 200
