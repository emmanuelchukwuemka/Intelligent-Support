from flask import Blueprint, request, jsonify, g
import json

import db
from auth_utils import token_required
from questions import QUESTIONS, SCALE
from ml.classifier import classify
from recommend_engine import get_recommendations

assessment_bp = Blueprint("assessment", __name__, url_prefix="/api/assessment")


@assessment_bp.get("/questions")
def questions():
    return jsonify({"questions": QUESTIONS, "scale": SCALE})


@assessment_bp.post("/submit")
@token_required
def submit():
    data = request.get_json(silent=True) or {}
    responses = data.get("responses")

    if not isinstance(responses, list) or len(responses) != len(QUESTIONS):
        return jsonify({"error": f"responses must be a list of {len(QUESTIONS)} integers (0-3)"}), 400
    try:
        responses = [int(r) for r in responses]
    except (TypeError, ValueError):
        return jsonify({"error": "responses must be integers"}), 400

    try:
        result = classify(responses)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    user_id = g.current_user["user_id"]
    row = db.execute(
        """
        INSERT INTO stress_assessments (user_id, responses_json, total_score, severity_level, stress_category)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING assessment_id, assessment_date
        """,
        (user_id, json.dumps(responses), result["total_score"], result["severity_level"], result["stress_category"]),
        returning=True,
    )

    recommendations = get_recommendations(user_id, result["severity_level"], result["stress_category"])

    return jsonify({
        "assessment_id": row["assessment_id"],
        "assessment_date": row["assessment_date"],
        "total_score": result["total_score"],
        "severity_level": result["severity_level"],
        "stress_category": result["stress_category"],
        "probabilities": result["probabilities"],
        "recommendations": recommendations,
    }), 201


@assessment_bp.get("/history")
@token_required
def history():
    rows = db.query_all(
        """
        SELECT assessment_id, assessment_date, total_score, severity_level, stress_category
        FROM stress_assessments WHERE user_id = %s
        ORDER BY assessment_date DESC
        """,
        (g.current_user["user_id"],),
    )
    return jsonify(rows)


@assessment_bp.get("/<int:assessment_id>")
@token_required
def get_assessment(assessment_id):
    row = db.query_one(
        """
        SELECT assessment_id, assessment_date, responses_json, total_score, severity_level, stress_category
        FROM stress_assessments WHERE assessment_id = %s AND user_id = %s
        """,
        (assessment_id, g.current_user["user_id"]),
    )
    if not row:
        return jsonify({"error": "Assessment not found"}), 404
    row["responses"] = json.loads(row.pop("responses_json"))
    return jsonify(row)
