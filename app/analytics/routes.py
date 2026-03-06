from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from ..extensions import db
from ..models.call_log import CallLog
from ..models.call_analytics import CallAnalytics

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/calls/summary', methods=['GET'])
@jwt_required()
def calls_summary():
    user_id = get_jwt_identity()
    total = CallLog.query.filter_by(user_id=user_id).count()
    completed = CallLog.query.filter_by(user_id=user_id, status=CallLog.STATUS_ENDED).count()
    failed = CallLog.query.filter_by(user_id=user_id, status=CallLog.STATUS_FAILED).count()

    avg_duration = db.session.query(func.avg(CallLog.duration_seconds)).filter(
        CallLog.user_id == user_id, CallLog.duration_seconds.isnot(None)
    ).scalar() or 0

    total_cost = db.session.query(func.sum(CallLog.cost)).filter(
        CallLog.user_id == user_id, CallLog.cost.isnot(None)
    ).scalar() or 0

    avg_interest = db.session.query(func.avg(CallAnalytics.interest_level)).filter(
        CallAnalytics.user_id == user_id, CallAnalytics.interest_level.isnot(None)
    ).scalar() or 0

    success_count = CallAnalytics.query.filter_by(user_id=user_id, success_evaluation='yes').count()

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
    positive = CallAnalytics.query.filter_by(user_id=user_id, sentiment='positive').count()
    negative = CallAnalytics.query.filter_by(user_id=user_id, sentiment='negative').count()
    neutral = CallAnalytics.query.filter_by(user_id=user_id, sentiment='neutral').count()

    return jsonify({'sentiment': {
        'positive': positive,
        'negative': negative,
        'neutral': neutral,
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
