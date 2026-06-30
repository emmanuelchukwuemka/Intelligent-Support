from flask import Blueprint, request, jsonify, g

import db
from auth_utils import token_required
from recommend_engine import get_recommendations

recommend_bp = Blueprint("recommend", __name__, url_prefix="/api/recommendations")


@recommend_bp.get("/<int:assessment_id>")
@token_required
def for_assessment(assessment_id):
    user_id = g.current_user["user_id"]
    assessment = db.query_one(
        "SELECT severity_level, stress_category FROM stress_assessments WHERE assessment_id = %s AND user_id = %s",
        (assessment_id, user_id),
    )
    if not assessment:
        return jsonify({"error": "Assessment not found"}), 404

    recs = get_recommendations(user_id, assessment["severity_level"], assessment["stress_category"])
    return jsonify(recs)


@recommend_bp.post("/rate")
@token_required
def rate_intervention():
    data = request.get_json(silent=True) or {}
    intervention_id = data.get("intervention_id")
    assessment_id = data.get("assessment_id")
    rating = data.get("rating")

    if intervention_id is None or rating is None:
        return jsonify({"error": "intervention_id and rating are required"}), 400
    try:
        rating = float(rating)
    except (TypeError, ValueError):
        return jsonify({"error": "rating must be a number"}), 400
    if not (1 <= rating <= 5):
        return jsonify({"error": "rating must be between 1 and 5"}), 400

    user_id = g.current_user["user_id"]
    existing = db.query_one(
        "SELECT id FROM user_interventions WHERE user_id = %s AND intervention_id = %s AND assessment_id IS NOT DISTINCT FROM %s",
        (user_id, intervention_id, assessment_id),
    )
    if existing:
        db.execute(
            "UPDATE user_interventions SET rating = %s, taken_at = NOW() WHERE id = %s",
            (rating, existing["id"]),
        )
    else:
        db.execute(
            """
            INSERT INTO user_interventions (user_id, intervention_id, assessment_id, rating)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, intervention_id, assessment_id, rating),
        )

    # Nudge the intervention's overall effectiveness_rating toward the new
    # rating (simple running average against existing user_interventions).
    agg = db.query_one(
        "SELECT AVG(rating) AS avg_rating FROM user_interventions WHERE intervention_id = %s AND rating IS NOT NULL",
        (intervention_id,),
    )
    if agg and agg["avg_rating"] is not None:
        db.execute(
            "UPDATE interventions SET effectiveness_rating = %s WHERE intervention_id = %s",
            (round(float(agg["avg_rating"]), 2), intervention_id),
        )

    return jsonify({"status": "ok"})
