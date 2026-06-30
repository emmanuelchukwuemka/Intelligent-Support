import os
import psycopg
from psycopg.rows import dict_row
from contextlib import contextmanager
import config

# When DATABASE_URL is set we are connecting to Neon (or any cloud PG).
# Neon's pooler endpoint uses PgBouncer in transaction mode, which does
# not support named prepared statements. Disable auto-prepare so every
# query uses the extended query protocol without statement caching.
# This is safe for both the Neon pooler and direct connections.
_DSN = config.DSN
_USE_CLOUD = bool(os.getenv("DATABASE_URL"))

if _USE_CLOUD and "sslmode" not in _DSN:
    _DSN += ("&" if "?" in _DSN else "?") + "sslmode=require"


@contextmanager
def get_conn():
    conn = psycopg.connect(
        _DSN,
        row_factory=dict_row,
        # None = never auto-prepare; required for PgBouncer transaction mode.
        prepare_threshold=None if _USE_CLOUD else 5,
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def query_one(sql, params=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()


def query_all(sql, params=None):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()


def execute(sql, params=None, returning=False):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            if returning:
                return cur.fetchone()
            return cur.rowcount
