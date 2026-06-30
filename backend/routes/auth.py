import re
from flask import Blueprint, request, jsonify, g

import db
from auth_utils import hash_password, verify_password, issue_token, token_required

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    email = (data.get("email") or "").strip()
    full_name = (data.get("full_name") or "").strip()
    age = data.get("age")
    gender = (data.get("gender") or "").strip() or None
    occupation = (data.get("occupation") or "").strip() or None

    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"error": "A valid email is required"}), 400

    if age is not None:
        try:
            age = int(age)
        except (TypeError, ValueError):
            return jsonify({"error": "Age must be a number"}), 400

    existing = db.query_one(
        "SELECT user_id FROM users WHERE username = %s OR email = %s", (username, email)
    )
    if existing:
        return jsonify({"error": "Username or email already in use"}), 409

    row = db.execute(
        """
        INSERT INTO users (username, password_hash, email, full_name, age, gender, occupation, role)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'user')
        RETURNING user_id, username, email, full_name, role
        """,
        (username, hash_password(password), email, full_name, age, gender, occupation),
        returning=True,
    )
    token = issue_token(row)
    return jsonify({"token": token, "user": row}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = db.query_one(
        "SELECT user_id, username, email, full_name, role, password_hash FROM users WHERE username = %s",
        (username,),
    )
    if not user or not verify_password(password, user["password_hash"]):
        return jsonify({"error": "Invalid username or password"}), 401

    token = issue_token(user)
    user.pop("password_hash")
    return jsonify({"token": token, "user": user})


@auth_bp.get("/me")
@token_required
def me():
    user = db.query_one(
        "SELECT user_id, username, email, full_name, age, gender, occupation, role, created_at FROM users WHERE user_id = %s",
        (g.current_user["user_id"],),
    )
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user)


@auth_bp.put("/me")
@token_required
def update_me():
    data = request.get_json(silent=True) or {}
    full_name = data.get("full_name")
    age = data.get("age")
    gender = data.get("gender")
    occupation = data.get("occupation")

    db.execute(
        """
        UPDATE users SET
            full_name = COALESCE(%s, full_name),
            age = COALESCE(%s, age),
            gender = COALESCE(%s, gender),
            occupation = COALESCE(%s, occupation)
        WHERE user_id = %s
        """,
        (full_name, age, gender, occupation, g.current_user["user_id"]),
    )
    user = db.query_one(
        "SELECT user_id, username, email, full_name, age, gender, occupation, role FROM users WHERE user_id = %s",
        (g.current_user["user_id"],),
    )
    return jsonify(user)
