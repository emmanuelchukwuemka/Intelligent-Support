from flask import Blueprint, request, jsonify, g

import db
from auth_utils import token_required

feedback_bp = Blueprint("feedback", __name__, url_prefix="/api/feedback")


@feedback_bp.post("")
@token_required
def submit_feedback():
    data = request.get_json(silent=True) or {}
    intervention_id = data.get("intervention_id")
    rating = data.get("rating")
    comments = (data.get("comments") or "").strip() or None

    if rating is not None:
        try:
            rating = int(rating)
        except (TypeError, ValueError):
            return jsonify({"error": "rating must be an integer"}), 400
        if not (1 <= rating <= 5):
            return jsonify({"error": "rating must be between 1 and 5"}), 400

    if rating is None and not comments:
        return jsonify({"error": "Provide a rating and/or comments"}), 400

    row = db.execute(
        """
        INSERT INTO feedback (user_id, intervention_id, rating, comments)
        VALUES (%s, %s, %s, %s)
        RETURNING feedback_id, submitted_at
        """,
        (g.current_user["user_id"], intervention_id, rating, comments),
        returning=True,
    )
    return jsonify(row), 201


@feedback_bp.get("/mine")
@token_required
def my_feedback():
    rows = db.query_all(
        """
        SELECT f.feedback_id, f.rating, f.comments, f.submitted_at, i.intervention_name
        FROM feedback f
        LEFT JOIN interventions i ON i.intervention_id = f.intervention_id
        WHERE f.user_id = %s ORDER BY f.submitted_at DESC
        """,
        (g.current_user["user_id"],),
    )
    return jsonify(rows)
