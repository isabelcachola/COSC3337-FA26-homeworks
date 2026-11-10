"""
Shared setup for the HW 4 tests.  You do not need to read or edit this.

Run the tests from the HW4 directory:

    python3 -m pytest tests/ -v                 # everything
    python3 -m pytest tests/ -v -k "2_1"        # only Question 2.1
    python3 -m pytest tests/ -v -k "2_3"        # only Question 2.3

Each question's checks start from freshly loaded data, so the tests RELOAD
soundwave_live.  When they finish, soundwave_live is restored from
soundwave_live.sql: tables you created there are gone, so re-run your scripts
if you want them back.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hw4lib as H  # noqa: E402


def pytest_configure(config):
    config.addinivalue_line("markers", "points(n): points this test is worth")


@pytest.fixture(scope="session")
def expected():
    return json.loads(H.EXPECTED.read_text(encoding="utf-8"))


@pytest.fixture(scope="session", autouse=True)
def restore_at_end():
    yield
    try:
        H.load(H.EXPORT)
    except Exception:
        pass


# ---------------------------------------------------------------- 2.1
@pytest.fixture(scope="session")
def fd_results():
    """{dataset: {Q: rows or error string}} for both datasets."""
    path = H.SUBMISSION / "fd_checks.sql"
    queries = H.read_fd_queries(path) if path.exists() else {}
    out = {}
    for dataset, sql_file in [("check", H.CHECK), ("export", H.EXPORT)]:
        H.load(sql_file)
        res = {}
        for q in ["Q1", "Q2", "Q3", "Q4", "Q5"]:
            if q not in queries:
                res[q] = f"no '-- {q}' section in fd_checks.sql"
                continue
            try:
                res[q] = [[str(v) for v in r] for r in H.rows(queries[q])]
            except Exception as e:  # noqa: BLE001
                res[q] = f"{q} failed to run: {e}"
        out[dataset] = res
    return out


# ---------------------------------------------------------------- 2.2
@pytest.fixture(scope="session")
def fix_state():
    H.load(H.FIXED)
    target = H.wide_rows()
    H.load(H.EXPORT)
    before = H.wide_rows()
    ok, err = H.run_sql_file(H.SUBMISSION / "fix.sql")
    after = H.wide_rows()
    return {"ok": ok, "err": err, "before": before, "after": after, "target": target}


# ---------------------------------------------------------------- 2.3 / 2.4
def load_fixed():
    """The export after a CORRECT fix.sql, so 2.3 is graded on its own,
    whatever your fix.sql does."""
    if H.REF_FIX:
        H.load(H.EXPORT)
        ok, err = H.run_sql_file(Path(H.REF_FIX))
        assert ok, err
    else:
        H.load(H.FIXED)


def build_normalized():
    load_fixed()
    return H.run_sql_file(H.SUBMISSION / "normalize.sql")


@pytest.fixture(scope="session")
def norm_state():
    load_fixed()
    state = {"wide_before": H.wide_rows()}
    ok, err = H.run_sql_file(H.SUBMISSION / "normalize.sql")
    state.update(ok=ok, err=err, tables={})
    if not ok:
        return state
    tables = H.student_tables()
    state.update(
        tables=tables,
        wide_after=H.wide_rows() if H.rows(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s AND table_name = %s",
            (H.DB, H.WIDE))[0][0] else None,
        pks=H.primary_keys(),
        fks=H.foreign_keys(),
        rules={r: H.rule_violations(r, tables) for r in ["R1", "R2", "R3", "R4", "R5", "R6"]},
        bcnf={t: H.bcnf_violation(c) for t, c in tables.items()},
    )
    state["lossless"] = H.lossless_report(tables) if tables and state["wide_after"] is not None else "no tables"
    return state


def require_normalized(state):
    if not state["ok"]:
        pytest.fail("normalize.sql failed: " + state["err"][-400:])
    if not state["tables"]:
        pytest.fail("normalize.sql created no tables")


def require_real_attempt(state):
    require_normalized(state)
    passed = sum(1 for v in state["rules"].values() if not v)
    if passed < 4:
        pytest.fail(f"only awarded when at least 4 of the 6 rule checks in 2.3(b) pass; {passed} do")


@pytest.fixture(scope="session")
def lossless_check_results(norm_state):
    """Your lossless_check.sql run on (a) your tables as built, (b) after one
    row is deleted from your largest table, (c) after one value is changed."""
    path = H.SUBMISSION / "lossless_check.sql"
    out = {}
    if not path.exists():
        return {k: "lossless_check.sql not found" for k in "abc"}
    query = H.strip_sql(path.read_text(encoding="utf-8"))
    if not norm_state["ok"] or not norm_state["tables"]:
        return {k: "needs a working normalize.sql (2.3)" for k in "abc"}

    def run():
        try:
            return H.rows(query)
        except Exception as e:  # noqa: BLE001
            return f"lossless_check.sql failed to run: {e}"

    tables = norm_state["tables"]
    pks = norm_state.get("pks", {})
    build_normalized()
    out["a"] = run()

    counts = {t: H.rows(f"SELECT COUNT(*) FROM `{t}`")[0][0] for t in tables}
    biggest = max(sorted(tables), key=lambda t: counts[t])
    H.execute("SET FOREIGN_KEY_CHECKS = 0", f"DELETE FROM `{biggest}` LIMIT 1")
    out["b"] = run()
    out["b_note"] = f"deleted one row of `{biggest}`"

    build_normalized()
    target = None
    for t in sorted(tables, key=lambda t: (counts[t], t)):
        for c in tables[t]:
            if c not in pks.get(t, set()):
                target = (t, c)
                break
        if target:
            break
    if target is None:
        out["c"] = "none of your tables has a column outside its primary key"
    else:
        t, c = target
        (dtype,), = H.rows("""SELECT data_type FROM information_schema.columns
                              WHERE table_schema = %s AND table_name = %s AND column_name = %s""",
                           (H.DB, t, c))
        if dtype in ("char", "varchar", "text"):
            new = f"CONCAT('~', SUBSTRING(`{c}`, 2))"
        elif dtype == "date":
            new = f"`{c}` + INTERVAL 1 DAY"
        else:
            new = f"`{c}` + 1"
        H.execute("SET FOREIGN_KEY_CHECKS = 0", f"UPDATE `{t}` SET `{c}` = {new} LIMIT 1")
        out["c"] = run()
        out["c_note"] = f"changed `{c}` in one row of `{t}`"
    return out
