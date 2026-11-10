"""
hw4lib.py — helpers shared by the HW 4 tests.  You do not need to read or edit
this file, but you are welcome to: everything the autograder checks is here.

Running the tests RELOADS soundwave_live several times (each check starts from
known data).  When the tests finish, soundwave_live is restored from
soundwave_live.sql, so any tables you created there are gone.  Re-run your own
scripts afterwards if you want them back.
"""

from __future__ import annotations

import functools
import getpass
import hashlib
import json
import itertools
import os
import re
import subprocess
from pathlib import Path

import mysql.connector

HW_DIR = Path(__file__).resolve().parent.parent
DATA = Path(__file__).resolve().parent / "data"

# Where things are.  The autograder points these at its own copies.
SUBMISSION = Path(os.environ.get("HW4_SUBMISSION", HW_DIR))
EXPORT = Path(os.environ.get("HW4_EXPORT", HW_DIR / "soundwave_live.sql"))
FIXED = Path(os.environ.get("HW4_FIXED", DATA / "soundwave_live_fixed.sql"))
CHECK = Path(os.environ.get("HW4_CHECK", DATA / "fd_check.sql"))
EXPECTED = Path(os.environ.get("HW4_EXPECTED", DATA / "expected.json"))
REF_FIX = os.environ.get("HW4_REF_FIX")      # autograder only

DB = "soundwave_live"
WIDE = "ticket_sale_wide"
COLUMNS = ["order_id", "order_date", "listener_id", "username", "email",
           "concert_id", "concert_date", "artist_id", "artist_name",
           "venue_id", "venue_name", "city", "capacity",
           "seat_section", "price", "quantity"]

# The business rules, exactly as in the handout.
RULES = {
    "R1": ({"listener_id"}, {"username", "email"}),
    "R2": ({"artist_id"}, {"artist_name"}),
    "R3": ({"venue_id"}, {"venue_name", "city", "capacity"}),
    "R4": ({"concert_id"}, {"concert_date", "artist_id", "venue_id"}),
    "R5": ({"concert_id", "seat_section"}, {"price"}),
    "R6": ({"order_id"}, {"order_date", "listener_id", "concert_id"}),
    "R7": ({"order_id", "seat_section"}, {"quantity"}),
}

DEFAULT_SOCKET = "/var/run/mysqld/mysqld.sock"


# ---------------------------------------------------------------- MySQL access
@functools.lru_cache(maxsize=1)
def _socket() -> str:
    if os.environ.get("DB_SOCKET"):
        return os.environ["DB_SOCKET"]
    if os.path.exists(DEFAULT_SOCKET):
        return DEFAULT_SOCKET
    try:
        out = subprocess.run(["mysql", "-N", "-B", "-e", "SELECT @@socket"], capture_output=True,
                             text=True, timeout=10, stdin=subprocess.DEVNULL)
        if out.returncode == 0 and os.path.exists(out.stdout.strip()):
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return DEFAULT_SOCKET


def _user() -> str:
    return os.environ.get("DB_USER") or getpass.getuser()


def connect():
    params = dict(user=_user(), password=os.environ.get("DB_PASSWORD", ""), database=DB,
                  ssl_disabled=True)
    if os.environ.get("DB_HOST"):
        params["host"] = os.environ["DB_HOST"]
    else:
        params["unix_socket"] = _socket()
    c = mysql.connector.connect(**params)
    c.autocommit = True
    return c


def _cli() -> list[str]:
    cmd = ["mysql", "--default-character-set=utf8mb4", "-u", _user()]
    if os.environ.get("DB_PASSWORD"):
        cmd.append("-p" + os.environ["DB_PASSWORD"])
    if os.environ.get("DB_HOST"):
        cmd += ["-h", os.environ["DB_HOST"], "--protocol=TCP"]
    else:
        cmd += ["--socket", _socket()]
    return cmd


def run_sql_file(path: Path, database: str | None = DB) -> tuple[bool, str]:
    """Run a .sql file through the `mysql` client, exactly as
    `mysql soundwave_live < file.sql` would.  Returns (ok, error text)."""
    if not Path(path).exists():
        return False, f"{Path(path).name} not found"
    cmd = _cli() + ([database] if database else [])
    with open(path, "rb") as f:
        p = subprocess.run(cmd, stdin=f, capture_output=True, timeout=300)
    err = p.stderr.decode("utf-8", "replace").strip()
    return p.returncode == 0, err


def load(path: Path) -> None:
    ok, err = run_sql_file(path, database=None)
    if not ok:
        raise RuntimeError(f"could not load {Path(path).name}: {err}")


def rows(sql: str, params=()) -> list[tuple]:
    c = connect()
    try:
        cur = c.cursor()
        cur.execute(sql, params)
        out = cur.fetchall()
        cur.close()
        return out
    finally:
        c.close()


def execute(*statements: str) -> None:
    c = connect()
    try:
        cur = c.cursor()
        for s in statements:
            cur.execute(s)
            if cur.with_rows:
                cur.fetchall()
        cur.close()
    finally:
        c.close()


def wide_rows() -> list[tuple]:
    return rows(f"SELECT {', '.join(COLUMNS)} FROM {WIDE} ORDER BY order_id, seat_section")


def strip_sql(text: str) -> str:
    """Remove -- comments, surrounding whitespace and the trailing semicolon."""
    lines = [ln for ln in text.splitlines() if not ln.strip().startswith("--")]
    return "\n".join(lines).strip().rstrip(";").strip()


def answer_hash(result: list[list[str]]) -> str:
    """The expected 2.1 answers are stored only as hashes of this form."""
    return hashlib.sha256(json.dumps(result).encode("utf-8")).hexdigest()


def read_fd_queries(path: Path) -> dict[str, str]:
    """Split fd_checks.sql on its `-- Q1` ... `-- Q5` header lines."""
    text = Path(path).read_text(encoding="utf-8")
    parts = re.split(r"^--\s*(Q[1-5])\b.*$", text, flags=re.M)
    return {parts[i]: strip_sql(parts[i + 1]) for i in range(1, len(parts), 2)}


# ---------------------------------------------------------------- FD theory
def closure(attrs, rules=RULES) -> set[str]:
    result = set(attrs)
    changed = True
    while changed:
        changed = False
        for lhs, rhs in rules.values():
            if lhs <= result and not rhs <= result:
                result |= rhs
                changed = True
    return result


def is_superkey(attrs, table_cols) -> bool:
    return set(table_cols) <= closure(attrs)


def bcnf_violation(table_cols):
    """None if the table is in BCNF under the business rules, else (alpha, beta):
    alpha -> beta holds (it is in F+), beta is inside the table, and alpha is
    not a superkey of the table.  Tests every subset alpha of the table's
    columns."""
    cols = sorted(table_cols)
    for k in range(1, len(cols)):
        for alpha in itertools.combinations(cols, k):
            cl = closure(alpha)
            beta = (cl & set(cols)) - set(alpha)
            if beta and not set(cols) <= cl:
                return set(alpha), beta
    return None


def rule_violations(rule: str, tables: dict[str, list[str]]) -> list[str]:
    """Tables that store rule's right side redundantly: they contain its left
    side and part of its right side, but its left side is not a superkey."""
    lhs, rhs = RULES[rule]
    bad = []
    for t, cols in tables.items():
        c = set(cols)
        if lhs <= c and (rhs & c) and not is_superkey(lhs, c):
            bad.append(t)
    return bad


# ---------------------------------------------------------------- your schema
def student_tables() -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for t, c in rows("""SELECT c.table_name, c.column_name
                        FROM information_schema.columns c
                        JOIN information_schema.tables t
                          ON t.table_schema = c.table_schema AND t.table_name = c.table_name
                        WHERE c.table_schema = %s AND t.table_type = 'BASE TABLE'
                          AND c.table_name <> %s
                        ORDER BY c.table_name, c.ordinal_position""", (DB, WIDE)):
        out.setdefault(t, []).append(c)
    return out


def primary_keys() -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for t, c in rows("""SELECT table_name, column_name FROM information_schema.key_column_usage
                        WHERE table_schema = %s AND constraint_name = 'PRIMARY'""", (DB,)):
        out.setdefault(t, set()).add(c)
    return out


def foreign_keys() -> list[tuple[str, frozenset, str]]:
    """(child table, child columns, parent table) for every foreign key."""
    fks: dict[tuple, dict] = {}
    for t, name, c, parent in rows("""SELECT table_name, constraint_name, column_name, referenced_table_name
                                      FROM information_schema.key_column_usage
                                      WHERE table_schema = %s AND referenced_table_name IS NOT NULL""", (DB,)):
        fks.setdefault((t, name), {"cols": set(), "parent": parent})["cols"].add(c)
    return [(t, frozenset(v["cols"]), v["parent"]) for (t, _), v in fks.items()]


def join_order(tables: dict[str, list[str]]) -> list[str] | None:
    """An order in which every table shares a column with an earlier one, so
    a chain of NATURAL JOINs never degenerates into a cross product."""
    names = sorted(tables, key=lambda t: (-len(tables[t]), t))
    if not names:
        return None
    order, seen = [names[0]], set(tables[names[0]])
    rest = names[1:]
    while rest:
        nxt = next((t for t in rest if set(tables[t]) & seen), None)
        if nxt is None:
            return None
        order.append(nxt)
        seen |= set(tables[nxt])
        rest.remove(nxt)
    return order


def lossless_report(tables: dict[str, list[str]]) -> str | None:
    """None if joining every table gives back exactly ticket_sale_wide."""
    order = join_order(tables)
    if order is None:
        return "your tables cannot all be joined: some table shares no column with the others"
    join = " NATURAL JOIN ".join(f"`{t}`" for t in order)
    cols = ", ".join(COLUMNS)
    (n_wide,), = rows(f"SELECT COUNT(*) FROM {WIDE}")
    (n_join,), = rows(f"SELECT COUNT(*) FROM {join}")
    (missing,), = rows(f"SELECT COUNT(*) FROM (SELECT {cols} FROM {WIDE} EXCEPT SELECT {cols} FROM {join}) x")
    (extra,), = rows(f"SELECT COUNT(*) FROM (SELECT {cols} FROM {join} EXCEPT SELECT {cols} FROM {WIDE}) x")
    if missing or extra or n_wide != n_join:
        return (f"joining your tables ({' ⋈ '.join(order)}) gives {n_join} rows; ticket_sale_wide has "
                f"{n_wide}. {missing} rows of ticket_sale_wide are missing from the join, and the join "
                f"has {extra} rows that are not in ticket_sale_wide")
    return None
