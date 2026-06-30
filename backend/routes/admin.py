from flask import Blueprint, request, jsonify

import db
from auth_utils import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


# ---- Users ----

@admin_bp.get("/users")
@admin_required
def list_users():
    rows = db.query_all(
        """
        SELECT u.user_id, u.username, u.email, u.full_name, u.role, u.created_at,
               COUNT(sa.assessment_id) AS assessment_count
        FROM users u
        LEFT JOIN stress_assessments sa ON sa.user_id = u.user_id
        GROUP BY u.user_id
        ORDER BY u.created_at DESC
        """
    )
    return jsonify(rows)


@admin_bp.patch("/users/<int:user_id>/role")
@admin_required
def update_role(user_id):
    data = request.get_json(silent=True) or {}
    role = data.get("role")
    if role not in ("user", "admin"):
        return jsonify({"error": "role must be 'user' or 'admin'"}), 400
    db.execute("UPDATE users SET role = %s WHERE user_id = %s", (role, user_id))
    return jsonify({"status": "ok"})


@admin_bp.delete("/users/<int:user_id>")
@admin_required
def delete_user(user_id):
    db.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
    return jsonify({"status": "ok"})


# ---- Knowledge base CRUD ----

@admin_bp.post("/knowledge")
@admin_required
def create_article():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    category = (data.get("category") or "").strip() or None
    content = (data.get("content") or "").strip()
    if not title or not content:
        return jsonify({"error": "title and content are required"}), 400

    row = db.execute(
        "INSERT INTO knowledge_base (title, category, content) VALUES (%s, %s, %s) RETURNING resource_id",
        (title, category, content),
        returning=True,
    )
    return jsonify(row), 201


@admin_bp.put("/knowledge/<int:resource_id>")
@admin_required
def update_article(resource_id):
    data = request.get_json(silent=True) or {}
    db.execute(
        """
        UPDATE knowledge_base SET
            title = COALESCE(%s, title),
            category = COALESCE(%s, category),
            content = COALESCE(%s, content)
        WHERE resource_id = %s
        """,
        (data.get("title"), data.get("category"), data.get("content"), resource_id),
    )
    return jsonify({"status": "ok"})


@admin_bp.delete("/knowledge/<int:resource_id>")
@admin_required
def delete_article(resource_id):
    db.execute("DELETE FROM knowledge_base WHERE resource_id = %s", (resource_id,))
    return jsonify({"status": "ok"})


# ---- Interventions (read mainly; effectiveness_rating is otherwise
# updated automatically by routes/recommend.py:rate_intervention) ----

@admin_bp.get("/interventions")
@admin_required
def list_interventions():
    rows = db.query_all("SELECT * FROM interventions ORDER BY intervention_type, target_severity")
    return jsonify(rows)


# ---- Reports ----

@admin_bp.get("/reports")
@admin_required
def reports():
    total_users = db.query_one("SELECT COUNT(*) AS c FROM users")["c"]
    total_assessments = db.query_one("SELECT COUNT(*) AS c FROM stress_assessments")["c"]
    severity_distribution = db.query_all(
        "SELECT severity_level, COUNT(*) AS c FROM stress_assessments GROUP BY severity_level"
    )
    category_distribution = db.query_all(
        "SELECT stress_category, COUNT(*) AS c FROM stress_assessments GROUP BY stress_category ORDER BY c DESC"
    )
    avg_score = db.query_one("SELECT AVG(total_score) AS avg FROM stress_assessments")["avg"]
    avg_feedback_rating = db.query_one("SELECT AVG(rating) AS avg FROM feedback WHERE rating IS NOT NULL")["avg"]
    top_interventions = db.query_all(
        "SELECT intervention_name, effectiveness_rating FROM interventions ORDER BY effectiveness_rating DESC LIMIT 5"
    )
    recent_assessments = db.query_all(
        """
        SELECT sa.assessment_id, u.username, sa.severity_level, sa.stress_category, sa.assessment_date
        FROM stress_assessments sa JOIN users u ON u.user_id = sa.user_id
        ORDER BY sa.assessment_date DESC LIMIT 10
        """
    )

    return jsonify({
        "total_users": total_users,
        "total_assessments": total_assessments,
        "average_score": round(float(avg_score), 2) if avg_score is not None else None,
        "average_feedback_rating": round(float(avg_feedback_rating), 2) if avg_feedback_rating is not None else None,
        "severity_distribution": severity_distribution,
        "category_distribution": category_distribution,
        "top_interventions": top_interventions,
        "recent_assessments": recent_assessments,
    })
