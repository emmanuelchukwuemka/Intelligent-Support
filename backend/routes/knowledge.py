from flask import Blueprint, request, jsonify

import db

knowledge_bp = Blueprint("knowledge", __name__, url_prefix="/api/knowledge")


@knowledge_bp.get("")
def list_articles():
    category = request.args.get("category")
    q = request.args.get("q")

    sql = "SELECT resource_id, title, category, content, created_at FROM knowledge_base WHERE 1=1"
    params = []
    if category:
        sql += " AND category = %s"
        params.append(category)
    if q:
        sql += " AND (title ILIKE %s OR content ILIKE %s)"
        like = f"%{q}%"
        params.extend([like, like])
    sql += " ORDER BY created_at DESC"

    rows = db.query_all(sql, tuple(params))
    return jsonify(rows)


@knowledge_bp.get("/categories")
def categories():
    rows = db.query_all("SELECT DISTINCT category FROM knowledge_base WHERE category IS NOT NULL ORDER BY category")
    return jsonify([r["category"] for r in rows])


@knowledge_bp.get("/<int:resource_id>")
def get_article(resource_id):
    row = db.query_one(
        "SELECT resource_id, title, category, content, created_at FROM knowledge_base WHERE resource_id = %s",
        (resource_id,),
    )
    if not row:
        return jsonify({"error": "Article not found"}), 404
    return jsonify(row)
