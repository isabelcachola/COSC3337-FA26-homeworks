#!/usr/bin/env python3
"""
validate_submission.py — check that your hw1.sql is in the right shape.

    python3 validate_submission.py hw1.sql

This checks FORMAT, not correctness.  It tells you whether the grader will be
able to read your file at all; it says nothing about whether your answers are
right.  Run it before you submit — a file the grader cannot parse loses points
that have nothing to do with SQL.

To also check that each query actually runs (this connects to MySQL and will
ask for your soundwave_ro password once):

    python3 validate_submission.py hw1.sql --check-runs

No installation required: it uses the `mysql` command already on your VM.
"""

from __future__ import annotations

import argparse
import getpass
import re
import shutil
import subprocess
import sys

EXPECTED = list(range(1, 13))

# Which database each question is asked against.  Fixed by the handout, not by
# anything in your file.
DB_FOR = {q: ("soundwave_small" if q >= 10 else "soundwave") for q in EXPECTED}

MARKER = re.compile(r"^\s*--\s*Q(\d+)\s*$")

GREEN, RED, YELLOW, DIM, RESET = (
    ("\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m")
    if sys.stdout.isatty() else ("", "", "", "", "")
)


def blank_noise(lines: list[str]) -> list[str]:
    """Return the file with string literals and comments blanked out, so that
    semicolons inside them are not miscounted.  Marker lines are preserved:
    they are the one kind of comment that carries meaning.

    Length and line structure are preserved, so positions still line up.
    """
    out: list[str] = []
    in_block = False
    in_str: str | None = None      # the quote character we are inside, if any

    for raw in lines:
        if not in_block and in_str is None and MARKER.match(raw):
            out.append(raw)
            continue

        buf: list[str] = []
        i = 0
        while i < len(raw):
            ch = raw[i]
            nxt = raw[i + 1] if i + 1 < len(raw) else ""

            if in_block:
                if ch == "*" and nxt == "/":
                    in_block = False
                    buf.append("  ")
                    i += 2
                    continue
                buf.append(" ")
                i += 1
                continue

            if in_str is not None:
                if ch == "\\":                     # backslash escape
                    buf.append("  ")
                    i += 2
                    continue
                if ch == in_str:
                    if nxt == in_str:              # doubled quote: '' or ""
                        buf.append("  ")
                        i += 2
                        continue
                    in_str = None
                    buf.append(" ")
                    i += 1
                    continue
                buf.append(" ")
                i += 1
                continue

            if ch == "/" and nxt == "*":
                in_block = True
                buf.append("  ")
                i += 2
                continue
            if (ch == "-" and nxt == "-") or ch == "#":
                buf.append(" " * (len(raw) - i))   # rest of line is a comment
                i = len(raw)
                continue
            if ch in ("'", '"', "`"):
                in_str = ch
                buf.append(" ")
                i += 1
                continue

            buf.append(ch)
            i += 1

        out.append("".join(buf))
    return out


def parse(path: str) -> tuple[dict[int, str], list[str]]:
    """Split the file into {question number: sql}.  Returns the answers and a
    list of structural problems found along the way."""
    problems: list[str] = []
    raw_lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    clean_lines = blank_noise(raw_lines)

    answers: dict[int, list[str]] = {}
    clean: dict[int, list[str]] = {}
    order: list[int] = []
    current: int | None = None

    for raw, cooked in zip(raw_lines, clean_lines):
        m = MARKER.match(raw)
        if m:
            q = int(m.group(1))
            if q in answers:
                problems.append(f"question Q{q} is marked more than once")
            answers.setdefault(q, [])
            clean.setdefault(q, [])
            order.append(q)
            current = q
            continue
        if current is None:
            if cooked.strip():
                problems.append(
                    "there is SQL before the first '-- Q1' marker; every "
                    "statement must sit under a marker")
                current = -1          # complain only once
            continue
        if current > 0:
            answers[current].append(raw)
            clean[current].append(cooked)

    if order != sorted(order):
        problems.append(f"markers are out of order: found {order}")

    result = {q: "\n".join(answers[q]).strip() for q in answers}
    for q in sorted(answers):
        body = "\n".join(clean[q]).strip()
        n = body.count(";")
        if not body:
            problems.append(f"Q{q} has no statement under its marker")
        elif n == 0:
            problems.append(f"Q{q} does not end in a semicolon")
        elif n > 1:
            problems.append(
                f"Q{q} contains {n} statements; each answer must be exactly one")
        elif not body.rstrip().endswith(";"):
            problems.append(f"Q{q} has text after its semicolon")
    return result, problems


def run_query(db: str, sql: str, user: str, password: str, host: str) -> str | None:
    """Execute one statement.  Returns None on success, else the error text."""
    cmd = [
        "mysql", "--batch", "--raw", "--skip-column-names",
        f"--user={user}", f"--host={host}", db,
    ]
    payload = "SET SESSION max_execution_time=5000;\n" + sql
    try:
        proc = subprocess.run(
            cmd, input=payload, capture_output=True, text=True, timeout=30,
            env={"MYSQL_PWD": password, "PATH": "/usr/bin:/bin:/usr/local/bin"},
        )
    except subprocess.TimeoutExpired:
        return ("query did not finish in 30 seconds — you have probably written "
                "a Cartesian product (a join with no ON condition)")
    if proc.returncode != 0:
        return proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else "failed"
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description="Check the format of your hw1.sql.")
    ap.add_argument("path", nargs="?", default="hw1.sql")
    ap.add_argument("--check-runs", action="store_true",
                    help="also execute each query to confirm it runs")
    ap.add_argument("--user", default="soundwave_ro")
    ap.add_argument("--host", default="localhost")
    args = ap.parse_args()

    try:
        answers, problems = parse(args.path)
    except FileNotFoundError:
        print(f"{RED}No such file: {args.path}{RESET}")
        print("Run this from the directory containing your hw1.sql.")
        sys.exit(1)

    print(f"Checking {args.path}\n")

    missing = [q for q in EXPECTED if q not in answers]
    extra = [q for q in answers if q not in EXPECTED]
    if missing:
        problems.append(f"no marker for: {', '.join('Q%d' % q for q in missing)}")
    if extra:
        problems.append(f"unexpected marker(s): {', '.join('Q%d' % q for q in extra)}")

    for q in EXPECTED:
        body = answers.get(q, "")
        if not body:
            print(f"  Q{q:<3} {RED}missing{RESET}")
        else:
            first = " ".join(body.split())[:64]
            print(f"  Q{q:<3} {GREEN}found{RESET}   {DIM}{first}{'...' if len(first) == 64 else ''}{RESET}")

    if args.check_runs and answers:
        if not shutil.which("mysql"):
            print(f"\n{YELLOW}No `mysql` command found — skipping the run check.{RESET}")
        else:
            password = getpass.getpass(f"\nMySQL password for {args.user}: ")
            print()
            for q in EXPECTED:
                body = answers.get(q, "")
                if not body:
                    continue
                err = run_query(DB_FOR[q], body, args.user, password, args.host)
                if err:
                    print(f"  Q{q:<3} {RED}error{RESET}   {err}")
                    problems.append(f"Q{q} does not run: {err}")
                else:
                    print(f"  Q{q:<3} {GREEN}runs{RESET}    against {DB_FOR[q]}")

    print()
    if problems:
        print(f"{RED}Not ready to submit — {len(problems)} problem(s):{RESET}")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)

    print(f"{GREEN}Format is good: all 12 answers found and well formed.{RESET}")
    print("This script only checks the format, not the correctness of your submission.")


if __name__ == "__main__":
    main()
