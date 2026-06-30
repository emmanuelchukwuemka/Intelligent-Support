import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

import config
from routes.auth import auth_bp
from routes.assessment import assessment_bp
from routes.recommend import recommend_bp
from routes.progress import progress_bp
from routes.knowledge import knowledge_bp
from routes.feedback import feedback_bp
from routes.admin import admin_bp

# Resolve the frontend directory relative to this file so it works both
# locally (backend/ + frontend/ siblings) and on Render.
FRONTEND_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
)

app = Flask(__name__, static_folder=None)
CORS(app, resources={r"/api/*": {"origins": config.CORS_ORIGIN}})

# ---- API blueprints (registered first so /api/* routes take priority) ----
app.register_blueprint(auth_bp)
app.register_blueprint(assessment_bp)
app.register_blueprint(recommend_bp)
app.register_blueprint(progress_bp)
app.register_blueprint(knowledge_bp)
app.register_blueprint(feedback_bp)
app.register_blueprint(admin_bp)


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


# ---- Frontend static file serving -----------------------------------
# All non-API paths are served from the frontend/ directory.
# Deep-link routes (e.g. /dashboard.html) resolve to the actual file.

@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def frontend(path):
    file_path = os.path.join(FRONTEND_DIR, path)
    if os.path.isfile(file_path):
        return send_from_directory(FRONTEND_DIR, path)
    # SPA-style fallback: unknown paths serve index.html
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.errorhandler(404)
def not_found(e):
    # API 404s return JSON; everything else falls through to frontend()
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.FLASK_PORT, debug=True)
