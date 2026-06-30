import os
import psycopg
from psycopg.rows import dict_row
from contextlib import contextmanager
import config

# Render's managed Postgres requires SSL. When DATABASE_URL is set we
# are running on Render; append sslmode=require to the URL if absent.
_DSN = config.DSN
if os.getenv("DATABASE_URL") and "sslmode" not in _DSN:
    _DSN += ("&" if "?" in _DSN else "?") + "sslmode=require"


@contextmanager
def get_conn():
    conn = psycopg.connect(_DSN, row_factory=dict_row)
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
