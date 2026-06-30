from flask import Blueprint, request, jsonify, g

import db
from auth_utils import token_required

progress_bp = Blueprint("progress", __name__, url_prefix="/api/progress")


@progress_bp.get("")
@token_required
def list_progress():
    rows = db.query_all(
        """
        SELECT progress_id, tracking_date, stress_level, mood_rating, notes
        FROM progress_tracking WHERE user_id = %s
        ORDER BY tracking_date ASC
        """,
        (g.current_user["user_id"],),
    )
    return jsonify(rows)


@progress_bp.post("")
@token_required
def add_progress():
    data = request.get_json(silent=True) or {}
    stress_level = data.get("stress_level")
    mood_rating = data.get("mood_rating")
    notes = (data.get("notes") or "").strip() or None

    try:
        stress_level = int(stress_level)
        mood_rating = int(mood_rating)
    except (TypeError, ValueError):
        return jsonify({"error": "stress_level and mood_rating must be integers"}), 400
    if not (1 <= stress_level <= 10) or not (1 <= mood_rating <= 10):
        return jsonify({"error": "stress_level and mood_rating must be between 1 and 10"}), 400

    row = db.execute(
        """
        INSERT INTO progress_tracking (user_id, stress_level, mood_rating, notes)
        VALUES (%s, %s, %s, %s)
        RETURNING progress_id, tracking_date, stress_level, mood_rating, notes
        """,
        (g.current_user["user_id"], stress_level, mood_rating, notes),
        returning=True,
    )
    return jsonify(row), 201


@progress_bp.get("/summary")
@token_required
def summary():
    user_id = g.current_user["user_id"]
    recent = db.query_all(
        """
        SELECT stress_level, mood_rating, tracking_date FROM progress_tracking
        WHERE user_id = %s ORDER BY tracking_date DESC LIMIT 7
        """,
        (user_id,),
    )
    older = db.query_all(
        """
        SELECT stress_level, mood_rating FROM progress_tracking
        WHERE user_id = %s ORDER BY tracking_date DESC OFFSET 7 LIMIT 7
        """,
        (user_id,),
    )

    def avg(rows, key):
        vals = [r[key] for r in rows]
        return round(sum(vals) / len(vals), 2) if vals else None

    recent_stress_avg = avg(recent, "stress_level")
    older_stress_avg = avg(older, "stress_level")
    trend = None
    if recent_stress_avg is not None and older_stress_avg is not None:
        trend = "improving" if recent_stress_avg < older_stress_avg else (
            "worsening" if recent_stress_avg > older_stress_avg else "stable"
        )

    return jsonify({
        "entries_count": len(recent),
        "recent_avg_stress": recent_stress_avg,
        "recent_avg_mood": avg(recent, "mood_rating"),
        "previous_avg_stress": older_stress_avg,
        "trend": trend,
    })
