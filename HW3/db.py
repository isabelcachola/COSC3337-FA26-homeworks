"""
db.py — PROVIDED.  Do not edit, and do not submit.

    from db import get_connection, QueryCounter

get_connection()
    Opens a connection to the soundwave_app database on your VM.  There is no
    password: MySQL recognises you from your VM login (the same way
    `mysql soundwave_app` works), which only works over MySQL's local socket,
    so that is how we connect.

QueryCounter(conn)
    Wraps a connection and counts every query sent through it.  The autograder
    uses exactly this to check 2.2, so you can use it to check yourself:

        conn = QueryCounter(get_connection())
        get_dashboard(conn, "L0001")
        print(conn.count)          # how many queries did that take?

The defaults below are right for your VM.  The autograder overrides them with
environment variables, which is the only reason those exist.
"""

from __future__ import annotations

import functools
import os
import subprocess

import mysql.connector

DEFAULT_SOCKET = "/var/run/mysqld/mysqld.sock"


@functools.lru_cache(maxsize=1)
def _find_socket() -> str:
    """Where is this machine's MySQL socket?  Ubuntu (the course VMs) keeps it
    in DEFAULT_SOCKET.  Anywhere else, ask the `mysql` command, which already
    knows how to connect."""
    if os.path.exists(DEFAULT_SOCKET):
        return DEFAULT_SOCKET
    try:
        out = subprocess.run(["mysql", "-N", "-B", "-e", "SELECT @@socket"],
                             capture_output=True, text=True, timeout=10,
                             stdin=subprocess.DEVNULL)
        path = out.stdout.strip()
        if out.returncode == 0 and path and os.path.exists(path):
            return path
    except (OSError, subprocess.SubprocessError):
        pass
    for path in ("/tmp/mysql.sock", "/opt/homebrew/var/mysql/mysql.sock"):
        if os.path.exists(path):
            return path
    return DEFAULT_SOCKET


def get_connection():
    """Return a new connection to soundwave_app.  autocommit is OFF: changes
    you make are not saved until you call conn.commit()."""
    params = dict(
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "soundwave_app"),
    )
    socket = os.environ.get("DB_SOCKET") or _find_socket()
    if os.environ.get("DB_HOST"):
        params["host"] = os.environ["DB_HOST"]
    else:
        params["unix_socket"] = socket
    params["ssl_disabled"] = True   # local socket: nothing to encrypt
    conn = mysql.connector.connect(**params)
    conn.autocommit = False
    return conn


class _CountingCursor:
    def __init__(self, cursor, counter):
        self._cursor = cursor
        self._counter = counter

    def execute(self, operation, params=None, *args, **kwargs):
        self._counter.count += 1
        self._counter.queries.append(operation)
        if params is None:
            return self._cursor.execute(operation, *args, **kwargs)
        return self._cursor.execute(operation, params, *args, **kwargs)

    def executemany(self, operation, seq_params, *args, **kwargs):
        self._counter.count += 1
        self._counter.queries.append(operation)
        return self._cursor.executemany(operation, seq_params, *args, **kwargs)

    def __iter__(self):
        return iter(self._cursor)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self._cursor.close()
        return False

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class QueryCounter:
    """A connection that counts queries.  Use it anywhere you would use the
    connection itself."""

    def __init__(self, conn):
        self._conn = conn
        self.count = 0
        self.queries: list[str] = []

    def cursor(self, *args, **kwargs):
        return _CountingCursor(self._conn.cursor(*args, **kwargs), self)

    def reset(self):
        self.count = 0
        self.queries = []

    def __getattr__(self, name):
        return getattr(self._conn, name)
