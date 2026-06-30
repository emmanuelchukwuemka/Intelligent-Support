import os
from dotenv import load_dotenv

load_dotenv()

# ---- Database -------------------------------------------------------
# Render injects DATABASE_URL as "postgres://..." (legacy prefix).
# psycopg3 requires "postgresql://...". We fix the prefix here.
_DATABASE_URL = os.getenv("DATABASE_URL")
if _DATABASE_URL:
    if _DATABASE_URL.startswith("postgres://"):
        _DATABASE_URL = "postgresql://" + _DATABASE_URL[len("postgres://"):]
    DSN = _DATABASE_URL
else:
    DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "stress_support")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DSN = f"host={DB_HOST} port={DB_PORT} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD}"

# ---- Auth -----------------------------------------------------------
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24 * 7

# ---- Server ---------------------------------------------------------
FLASK_PORT = int(os.getenv("PORT", os.getenv("FLASK_PORT", "5000")))
CORS_ORIGIN = os.getenv("CORS_ORIGIN", "*")
