"""Database helpers: one connection per request, parameterized queries only."""
import getpass
import os
from datetime import date, datetime

import pymysql
import pymysql.cursors


def load_env():
    """Read demo/.env into os.environ (real environment variables win)."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip("\"'"))
    except FileNotFoundError:
        pass


load_env()


def get_conn():
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT") or 3306),
        user=os.environ.get("DB_USER") or getpass.getuser(),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "club_events"),
        unix_socket=os.environ.get("DB_SOCKET") or None,
        cursorclass=pymysql.cursors.DictCursor,
    )


def _jsonable(row):
    # JSON has no datetime type; send ISO 8601 strings the browser can parse.
    return {k: v.isoformat() if isinstance(v, (datetime, date)) else v
            for k, v in row.items()}


def query(sql, params=()):
    """Run a SELECT. `params` fill the %s placeholders; the driver escapes them."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return [_jsonable(r) for r in cur.fetchall()]
    finally:
        conn.close()


def execute(sql, params=()):
    """Run an INSERT/UPDATE/DELETE and commit. Returns the affected row count."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            n = cur.execute(sql, params)
        conn.commit()
        return n
    finally:
        conn.close()
