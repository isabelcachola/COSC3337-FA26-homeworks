#!/usr/bin/env python3
"""COSC 3337 HW2 self-check (same checks the autograder runs).

Usage (on your VM, from the folder containing schema.sql):
    conda activate cosc3337
    python hw2_check.py schema.sql
If you log in to MySQL with a password, add: --user YOUR_MYSQL_USER --password YOUR_MYSQL_PASSWORD

Requires: MySQL 8.0.16+, the `mysql` command-line client, and the
mysql-connector-python package (see Part 0 of the handout).
WARNING: this script drops and recreates the database `hw2_dive`.
"""
import argparse, os, subprocess, sys
import mysql.connector

DB = "hw2_dive"

# ---------------------------------------------------------------- contract
CONTRACT = {
    "customer":   ["customer_id", "email", "first_name", "last_name", "cert_level"],
    "divemaster": ["divemaster_id", "first_name", "last_name", "pro_number"],
    "boat":       ["boat_id", "name", "capacity"],
    "trip":       ["trip_id", "boat_id", "divemaster_id", "trip_date", "price"],
    "dive":       ["trip_id", "dive_no", "max_depth_m", "bottom_time_min"],
    "booking":    ["customer_id", "trip_id", "amount_paid"],
}
REQUIRED_FKS = [("trip", "boat"), ("trip", "divemaster"), ("booking", "customer"),
                ("booking", "trip"), ("dive", "trip")]

# ---------------------------------------------------------------- fixture
FIXTURE = [
    "INSERT INTO customer (customer_id, email, first_name, last_name, cert_level) VALUES "
    "(1,'ana@example.com','Ana','Diaz','Advanced'), (2,'ben@example.com','Ben','Okafor','Open Water')",
    "INSERT INTO divemaster (divemaster_id, first_name, last_name, pro_number) VALUES (1,'Carla','Ruiz','PRO-1001')",
    "INSERT INTO boat (boat_id, name, capacity) VALUES (1,'Manta',12)",
    "INSERT INTO trip (trip_id, boat_id, divemaster_id, trip_date, price) VALUES (1,1,1,'2026-11-14',95.00)",
    "INSERT INTO dive (trip_id, dive_no, max_depth_m, bottom_time_min) VALUES (1,1,18,45)",
    "INSERT INTO booking (customer_id, trip_id, amount_paid) VALUES (1,1,95.00)",
]

# ---------------------------------------------------------------- tests
# (id, description, setup statements, statement under test, expected, check query)
# expected: "ok" or a set of accepted MySQL error codes.
FK_CHILD, FK_PARENT, DUP, NOT_NULL, CHECK, TRUNC, RANGE = 1452, 1451, 1062, 1048, 3819, 1265, 1264
TRIP2 = "INSERT INTO trip (trip_id, boat_id, divemaster_id, trip_date, price) VALUES (2,1,1,'2026-11-21',80.00)"
TESTS = [
    ("T01", "Add a new customer",
     [], "INSERT INTO customer (customer_id, email, first_name, last_name, cert_level) "
         "VALUES (3,'cy@example.com','Cy','Tran','Rescue')", "ok", None),
    ("T02", "Add a second trip on the same boat with the same divemaster",
     [], TRIP2, "ok", None),
    ("T03", "A second customer books trip 1 with a partial deposit",
     [], "INSERT INTO booking (customer_id, trip_id, amount_paid) VALUES (2,1,50.00)", "ok", None),
    ("T04", "Add dive 2 to trip 1",
     [], "INSERT INTO dive (trip_id, dive_no, max_depth_m, bottom_time_min) VALUES (1,2,12,50)", "ok", None),
    ("T05", "Dive number 1 is reused on a different trip",
     [TRIP2], "INSERT INTO dive (trip_id, dive_no, max_depth_m, bottom_time_min) VALUES (2,1,15,40)", "ok", None),
    ("T06", "A customer who already booked one trip books another",
     [TRIP2], "INSERT INTO booking (customer_id, trip_id, amount_paid) VALUES (1,2,0)", "ok", None),
    ("T07", "Cancelling (deleting) a trip with no bookings also deletes its dives",
     [TRIP2, "INSERT INTO dive (trip_id, dive_no, max_depth_m, bottom_time_min) VALUES (2,1,15,40),(2,2,10,50)"],
     "DELETE FROM trip WHERE trip_id = 2", "ok",
     ("SELECT COUNT(*) FROM dive WHERE trip_id = 2", 0)),
    ("T08", "Two customers with the same email",
     [], "INSERT INTO customer (customer_id, email, first_name, last_name, cert_level) "
         "VALUES (3,'ana@example.com','Anabel','Diaz','Advanced')", {DUP}, None),
    ("T09", "Certification level that is not on the shop's list",
     [], "INSERT INTO customer (customer_id, email, first_name, last_name, cert_level) "
         "VALUES (3,'cy@example.com','Cy','Tran','Expert')", {CHECK, TRUNC}, None),
    ("T10", "Boat with capacity 0",
     [], "INSERT INTO boat (boat_id, name, capacity) VALUES (2,'Remora',0)", {CHECK}, None),
    ("T11", "Two divemasters with the same PADI pro number",
     [], "INSERT INTO divemaster (divemaster_id, first_name, last_name, pro_number) "
         "VALUES (2,'Dev','Shah','PRO-1001')", {DUP}, None),
    ("T12", "Trip with no boat",
     [], "INSERT INTO trip (trip_id, boat_id, divemaster_id, trip_date, price) VALUES (2,NULL,1,'2026-11-21',80)",
     {NOT_NULL}, None),
    ("T13", "Trip on a boat that does not exist",
     [], "INSERT INTO trip (trip_id, boat_id, divemaster_id, trip_date, price) VALUES (2,99,1,'2026-11-21',80)",
     {FK_CHILD}, None),
    ("T14", "Booking for a customer who does not exist",
     [], "INSERT INTO booking (customer_id, trip_id, amount_paid) VALUES (99,1,0)", {FK_CHILD}, None),
    ("T15", "Booking for a trip that does not exist",
     [], "INSERT INTO booking (customer_id, trip_id, amount_paid) VALUES (2,99,0)", {FK_CHILD}, None),
    ("T16", "The same customer books the same trip twice",
     [], "INSERT INTO booking (customer_id, trip_id, amount_paid) VALUES (1,1,10)", {DUP}, None),
    ("T17", "Booking with a negative amount paid",
     [], "INSERT INTO booking (customer_id, trip_id, amount_paid) VALUES (2,1,-10)", {CHECK, RANGE}, None),
    ("T18", "Two dives with the same number on the same trip",
     [], "INSERT INTO dive (trip_id, dive_no, max_depth_m, bottom_time_min) VALUES (1,1,10,30)", {DUP}, None),
    ("T19", "Dive deeper than the 40 m recreational limit",
     [], "INSERT INTO dive (trip_id, dive_no, max_depth_m, bottom_time_min) VALUES (1,2,45,20)", {CHECK}, None),
    ("T20", "Removing a boat that has trips on record",
     [], "DELETE FROM boat WHERE boat_id = 1", {FK_PARENT}, None),
]

CODE_NAMES = {FK_CHILD: "foreign key", FK_PARENT: "foreign key (parent row)", DUP: "duplicate key",
              NOT_NULL: "NOT NULL", CHECK: "CHECK", TRUNC: "ENUM/data truncated", RANGE: "out of range"}


SOCKET_PATHS = ["/var/run/mysqld/mysqld.sock", "/run/mysqld/mysqld.sock", "/tmp/mysql.sock"]


def connect(args, **extra):
    """Connect over the local socket when possible, otherwise over TCP.

    The socket lets Ubuntu's default MySQL root account (auth_socket, no password)
    log in when the script is run as the Linux root user.
    """
    last = None
    for mode in args.modes:
        kw = dict(user=args.user, password=args.password, **extra)
        if mode == "tcp":
            kw["host"] = args.host
        else:
            kw["unix_socket"] = mode
        try:
            conn = mysql.connector.connect(**kw)
            args.modes = [mode]          # remember what worked
            return conn
        except mysql.connector.Error as e:
            last = e
    raise last


def load_schema(path, args):
    cmd = ["mysql", f"-u{args.user}"]
    mode = args.modes[0]
    cmd += ["--protocol=TCP", f"-h{args.host}"] if mode == "tcp" else [f"--socket={mode}"]
    if args.password:
        cmd.append(f"-p{args.password}")
    with open(path, "rb") as f:
        r = subprocess.run(cmd, stdin=f, capture_output=True)
    return r.returncode == 0, r.stderr.decode(errors="replace").replace(
        "mysql: [Warning] Using a password on the command line interface can be insecure.\n", "").strip()


def q(cur, sql, params=()):
    cur.execute(sql, params)
    return cur.fetchall()


def structural(cur):
    out = []
    tables = {r[0] for r in q(cur, "SELECT table_name FROM information_schema.tables "
                                   "WHERE table_schema=%s AND table_type='BASE TABLE'", (DB,))}
    # S2 contract
    problems = []
    for t, cols in CONTRACT.items():
        if t not in tables:
            problems.append(f"missing table {t}")
            continue
        info = {r[0]: r[1:] for r in q(cur, "SELECT column_name, is_nullable, column_default, extra "
                                            "FROM information_schema.columns WHERE table_schema=%s AND table_name=%s",
                                       (DB, t))}
        for c in cols:
            if c not in info:
                problems.append(f"missing column {t}.{c}")
        for c, (nullable, default, extra) in info.items():
            if c not in cols and nullable == "NO" and default is None and "auto_increment" not in extra:
                problems.append(f"extra column {t}.{c} is NOT NULL with no DEFAULT")
    out.append(("S2", "Contract tables and columns present; extra columns nullable or defaulted", 3,
                not problems, "; ".join(problems)))
    # S3 PKs
    pk_tables = {r[0] for r in q(cur, "SELECT table_name FROM information_schema.table_constraints "
                                      "WHERE table_schema=%s AND constraint_type='PRIMARY KEY'", (DB,))}
    nopk = sorted(tables - pk_tables)
    out.append(("S3", "Every table has a primary key", 2, not nopk, ", ".join(nopk)))
    # S4 dive PK
    dive_pk = {r[0] for r in q(cur, "SELECT column_name FROM information_schema.key_column_usage "
                                    "WHERE table_schema=%s AND table_name='dive' AND constraint_name='PRIMARY'", (DB,))}
    out.append(("S4", "dive's primary key is (trip_id, dive_no)", 2, dive_pk == {"trip_id", "dive_no"},
                f"found ({', '.join(sorted(dive_pk))})"))
    # S5 FKs
    fks = {(r[0], r[1]) for r in q(cur, "SELECT table_name, referenced_table_name FROM "
                                        "information_schema.referential_constraints WHERE constraint_schema=%s", (DB,))}
    missing = [f"{a} -> {b}" for a, b in REQUIRED_FKS if (a, b) not in fks]
    out.append(("S5", "Required foreign keys exist", 3, not missing, "missing " + ", ".join(missing)))
    # S6 CHECK / UNIQUE counts
    n_check = q(cur, "SELECT COUNT(*) FROM information_schema.table_constraints "
                     "WHERE table_schema=%s AND constraint_type='CHECK'", (DB,))[0][0]
    n_uniq = q(cur, "SELECT COUNT(*) FROM information_schema.table_constraints "
                    "WHERE table_schema=%s AND constraint_type='UNIQUE'", (DB,))[0][0]
    out.append(("S6", "At least 3 CHECK and 2 UNIQUE constraints", 1, n_check >= 3 and n_uniq >= 2,
                f"found {n_check} CHECK, {n_uniq} UNIQUE"))
    # S7 engine
    bad = [r[0] for r in q(cur, "SELECT table_name FROM information_schema.tables WHERE table_schema=%s "
                                "AND table_type='BASE TABLE' AND engine<>'InnoDB'", (DB,))]
    out.append(("S7", "All tables use InnoDB", 1, not bad, ", ".join(bad)))
    return out


def run_tests(conn):
    results = []
    cur = conn.cursor()
    for tid, desc, setup, stmt, expected, check in TESTS:
        conn.start_transaction()
        try:
            try:
                for s in setup:
                    cur.execute(s)
            except mysql.connector.Error as e:
                results.append((tid, desc, False, f"setup failed: {e.errno} {e.msg}"))
                continue
            err = None
            try:
                cur.execute(stmt)
            except mysql.connector.Error as e:
                err = e
            if expected == "ok":
                if err:
                    results.append((tid, desc, False, f"expected success, got error {err.errno}: {err.msg}"))
                elif check:
                    got = q(cur, check[0])[0][0]
                    results.append((tid, desc, got == check[1],
                                    "" if got == check[1] else f"`{check[0]}` returned {got}, expected {check[1]}"))
                else:
                    results.append((tid, desc, True, ""))
            else:
                want = " or ".join(f"{c} ({CODE_NAMES[c]})" for c in sorted(expected))
                if err is None:
                    results.append((tid, desc, False, f"expected rejection with {want}, but it succeeded"))
                elif err.errno in expected:
                    results.append((tid, desc, True, ""))
                else:
                    results.append((tid, desc, False, f"rejected for the wrong reason: {err.errno} {err.msg} "
                                                      f"(expected {want})"))
        finally:
            conn.rollback()
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("schema")
    ap.add_argument("--user", default="root")
    ap.add_argument("--password", default="")
    ap.add_argument("--host", default="localhost")
    args = ap.parse_args()
    args.modes = ([p for p in SOCKET_PATHS if os.path.exists(p)][:1] if args.host == "localhost" else []) + ["tcp"]

    try:
        conn0 = connect(args)
    except mysql.connector.Error as e:
        print(f"Could not connect to MySQL: {e.errno} {e.msg}")
        if e.errno in (2002, 2003):
            print("  -> Is the MySQL server running? Try: sudo systemctl start mysql")
        elif e.errno == 1698:
            print(f"  -> MySQL user '{args.user}' logs in without a password only when this script runs as the\n"
                  f"     Linux user of the same name (e.g., run it as root for MySQL root), or pass\n"
                  f"     --user and --password for a MySQL account that has a password.")
        elif e.errno == 1045:
            print("  -> Check the --user and --password you passed.")
        sys.exit(1)
    c0 = conn0.cursor()
    ver = q(c0, "SELECT VERSION()")[0][0]
    c0.execute(f"DROP DATABASE IF EXISTS {DB}")
    conn0.close()

    total, earned = 0, 0
    print(f"MySQL {ver}\n\n== Part 2.1: structural checks (15 pts) ==")
    ok, err = load_schema(args.schema, args)
    total += 3
    if not ok:
        print(f"[FAIL] S1 schema.sql runs without errors (0/3)\n       {err}")
        print("\nschema.sql must load cleanly before anything else can be checked.  Score: 0/35")
        sys.exit(1)
    print("[PASS] S1 schema.sql runs without errors (3/3)")
    earned += 3

    conn = connect(args, database=DB, autocommit=True)
    cur = conn.cursor()
    cur.execute("SET SESSION sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,"
                "ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'")
    for sid, desc, pts, passed, detail in structural(cur):
        total += pts
        earned += pts if passed else 0
        print(f"[{'PASS' if passed else 'FAIL'}] {sid} {desc} ({pts if passed else 0}/{pts})"
              + ("" if passed or not detail else f"\n       {detail}"))

    print("\n== Part 2.2: constraint tests (20 pts) ==")
    try:
        for s in FIXTURE:
            cur.execute(s)
    except mysql.connector.Error as e:
        print(f"Could not load the test fixture: {e.errno} {e.msg}\n"
              f"  -> check that the contract columns exist and extra columns allow NULL or have a DEFAULT.")
        print(f"\nScore: {earned}/{total + 20} (autograded portion)")
        sys.exit(1)
    conn.autocommit = False
    for tid, desc, passed, detail in run_tests(conn):
        total += 1
        earned += 1 if passed else 0
        print(f"[{'PASS' if passed else 'FAIL'}] {tid} {desc}" + ("" if passed else f"\n       {detail}"))

    print(f"\nScore: {earned}/{total} (autograded portion only; design is graded by hand)")


if __name__ == "__main__":
    main()