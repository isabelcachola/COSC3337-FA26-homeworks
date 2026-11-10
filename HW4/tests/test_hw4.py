"""
HW 4 tests.  The autograder runs exactly these tests, on a DIFFERENT copy of
the data (different listeners, concerts, orders and broken rows).
"""

from __future__ import annotations

import pytest

import hw4lib as H

points = pytest.mark.points

RULE_TEXT = {
    "R1": "listener_id -> username, email",
    "R2": "artist_id -> artist_name",
    "R3": "venue_id -> venue_name, city, capacity",
    "R4": "concert_id -> concert_date, artist_id, venue_id",
    "R5": "concert_id, seat_section -> price",
    "R6": "order_id -> order_date, listener_id, concert_id",
}
QUERY_RULE = {"Q1": "R1", "Q2": "R3", "Q3": "R4", "Q4": "R5", "Q5": "R6"}


# =====================================================================
# 2.1  Find the rule violations  (15 points)
# =====================================================================
def _check_query(q, fd_results, expected):
    for dataset, label in [("check", "the test copy, where every rule is broken"),
                           ("export", "your copy of the export (soundwave_live.sql)")]:
        got = fd_results[dataset][q]
        if isinstance(got, str):
            pytest.fail(got)
        assert H.answer_hash(got) == expected["fd_checks"][dataset][q], (
            f"{q} checks {QUERY_RULE[q]} ({RULE_TEXT[QUERY_RULE[q]]}). On {label} it does not return "
            f"exactly the right rows (it returned {len(got)}). Check the columns, the order, and that "
            "every right-hand-side attribute is checked.")


@points(3)
def test_2_1_q1(fd_results, expected):
    """Q1 finds every violation of R1"""
    _check_query("Q1", fd_results, expected)


@points(3)
def test_2_1_q2(fd_results, expected):
    """Q2 finds every violation of R3"""
    _check_query("Q2", fd_results, expected)


@points(3)
def test_2_1_q3(fd_results, expected):
    """Q3 finds every violation of R4"""
    _check_query("Q3", fd_results, expected)


@points(3)
def test_2_1_q4(fd_results, expected):
    """Q4 finds every violation of R5"""
    _check_query("Q4", fd_results, expected)


@points(3)
def test_2_1_q5(fd_results, expected):
    """Q5 finds every violation of R6"""
    _check_query("Q5", fd_results, expected)


# =====================================================================
# 2.2  Repair the export  (10 points)
# =====================================================================
COL = {c: i for i, c in enumerate(H.COLUMNS)}


def _fix_ran(fix_state):
    if not fix_state["ok"]:
        pytest.fail("fix.sql failed: " + fix_state["err"][-400:])


@points(4)
def test_2_2_a_rules_hold(fix_state):
    """after fix.sql, every rule R1-R7 holds"""
    _fix_ran(fix_state)
    after = fix_state["after"]
    for rule, (lhs, rhs) in H.RULES.items():
        seen: dict = {}
        for r in after:
            seen.setdefault(tuple(r[COL[a]] for a in sorted(lhs)), set()).add(
                tuple(r[COL[a]] for a in sorted(rhs)))
        bad = sorted(k for k, v in seen.items() if len(v) > 1)
        assert not bad, f"{rule} ({RULE_TEXT.get(rule, 'order_id, seat_section -> quantity')}) is still violated, e.g. for {bad[0]}"


@points(4)
def test_2_2_b_matches_repair(fix_state):
    """every repaired value is the newest one, and nothing else changed"""
    _fix_ran(fix_state)
    after, target = fix_state["after"], fix_state["target"]
    by_key = {(r[COL["order_id"]], r[COL["seat_section"]]): r for r in after}
    wrong = []
    for t in target:
        r = by_key.get((t[COL["order_id"]], t[COL["seat_section"]]))
        if r is None:
            wrong.append(f"row ({t[0]}, {t[COL['seat_section']]}) is missing")
        elif r != t:
            col = next(c for c, i in COL.items() if r[i] != t[i])
            wrong.append(f"row ({t[0]}, {t[COL['seat_section']]}) has the wrong {col}")
        if len(wrong) >= 3:
            break
    assert not wrong, ("ticket_sale_wide does not match the correctly repaired export: "
                       + "; ".join(wrong) + ". The correct value is the one on the row with the largest order_id.")


@points(2)
def test_2_2_c_same_rows(fix_state):
    """no rows were added or deleted (only awarded if every rule holds afterwards)"""
    test_2_2_a_rules_hold(fix_state)
    keys = lambda rows: sorted((r[COL["order_id"]], r[COL["seat_section"]]) for r in rows)  # noqa: E731
    assert len(fix_state["after"]) == len(fix_state["before"]), (
        f"ticket_sale_wide had {len(fix_state['before'])} rows, now {len(fix_state['after'])}")
    assert keys(fix_state["after"]) == keys(fix_state["before"]), "some rows' order_id or seat_section changed"


# =====================================================================
# 2.3  Normalize  (20 points)
# =====================================================================
from conftest import require_normalized, require_real_attempt  # noqa: E402


@points(2)
def test_2_3_a_runs_and_covers(norm_state):
    """normalize.sql runs, uses exactly the 16 columns, and leaves ticket_sale_wide unchanged"""
    require_normalized(norm_state)
    used = set().union(*map(set, norm_state["tables"].values()))
    extra = sorted(used - set(H.COLUMNS))
    missing = sorted(set(H.COLUMNS) - used)
    assert not extra, f"columns that are not in ticket_sale_wide: {extra} (no new columns, no renaming)"
    assert not missing, f"columns of ticket_sale_wide that none of your tables has: {missing}"
    assert norm_state["wide_after"] is not None, "ticket_sale_wide was dropped"
    assert norm_state["wide_after"] == norm_state["wide_before"], "ticket_sale_wide was changed"


def _rule(norm_state, rule):
    require_normalized(norm_state)
    bad = norm_state["rules"][rule]
    lhs = ", ".join(sorted(H.RULES[rule][0]))
    assert not bad, (f"{rule} ({RULE_TEXT[rule]}) is stored redundantly in {bad}: "
                     f"each holds {lhs} and part of the right side, but {lhs} is not a key of it")


@points(1)
def test_2_3_b_r1(norm_state):
    """no table stores R1's right side redundantly"""
    _rule(norm_state, "R1")


@points(1)
def test_2_3_b_r2(norm_state):
    """no table stores R2's right side redundantly"""
    _rule(norm_state, "R2")


@points(1)
def test_2_3_b_r3(norm_state):
    """no table stores R3's right side redundantly"""
    _rule(norm_state, "R3")


@points(1)
def test_2_3_b_r4(norm_state):
    """no table stores R4's right side redundantly"""
    _rule(norm_state, "R4")


@points(1)
def test_2_3_b_r5(norm_state):
    """no table stores R5's right side redundantly"""
    _rule(norm_state, "R5")


@points(1)
def test_2_3_b_r6(norm_state):
    """no table stores R6's right side redundantly"""
    _rule(norm_state, "R6")


@points(2)
def test_2_3_c_bcnf(norm_state):
    """every table is in BCNF"""
    require_real_attempt(norm_state)
    bad = {t: v for t, v in norm_state["bcnf"].items() if v}
    msgs = [f"`{t}`: {', '.join(sorted(a))} -> {', '.join(sorted(b))} holds, but "
            f"{', '.join(sorted(a))} is not a superkey of `{t}`" for t, (a, b) in sorted(bad.items())]
    assert not bad, "not in BCNF: " + "; ".join(msgs)


@points(6)
def test_2_3_d_lossless(norm_state):
    """joining your tables gives back exactly ticket_sale_wide"""
    require_real_attempt(norm_state)
    assert norm_state["lossless"] is None, norm_state["lossless"]


@points(2)
def test_2_3_e_primary_keys(norm_state):
    """every table has a primary key, and it is a candidate key of that table"""
    require_real_attempt(norm_state)
    problems = []
    for t, cols in sorted(norm_state["tables"].items()):
        pk = norm_state["pks"].get(t)
        if not pk:
            problems.append(f"`{t}` has no primary key")
        elif not H.is_superkey(pk, cols):
            problems.append(f"`{t}`'s primary key ({', '.join(sorted(pk))}) does not determine all its columns")
        else:
            for a in sorted(pk):
                if H.is_superkey(pk - {a}, cols):
                    problems.append(f"`{t}`'s primary key ({', '.join(sorted(pk))}) is not minimal: "
                                    f"drop {a}")
                    break
    assert not problems, "; ".join(problems)


@points(2)
def test_2_3_f_foreign_keys(norm_state):
    """every table that holds another table's primary key declares a foreign key to it"""
    require_real_attempt(norm_state)
    pks, tables = norm_state["pks"], norm_state["tables"]
    have = {(child, cols, parent) for child, cols, parent in norm_state["fks"]}
    missing = []
    for child, cols in sorted(tables.items()):
        for parent, ppk in sorted(pks.items()):
            if parent == child or parent not in tables:
                continue
            if ppk <= set(cols) and ppk != pks.get(child, set()):
                if (child, frozenset(ppk), parent) not in have:
                    missing.append(f"`{child}`({', '.join(sorted(ppk))}) -> `{parent}`")
    assert not missing, "missing foreign keys: " + "; ".join(missing)


# =====================================================================
# 2.4  Prove it  (5 points)
# =====================================================================
def _result(res, key):
    if isinstance(res[key], str):
        pytest.fail(res[key])
    return res[key]


@points(2)
def test_2_4_b_detects_missing_row(lossless_check_results):
    """lossless_check.sql reports rows when one row is deleted from your largest table"""
    got = _result(lossless_check_results, "b")
    assert len(got) >= 1, f"after we {lossless_check_results['b_note']}, your query returned no rows"


@points(2)
def test_2_4_c_detects_changed_value(lossless_check_results):
    """lossless_check.sql reports rows when one value is changed"""
    got = _result(lossless_check_results, "c")
    assert len(got) >= 1, f"after we {lossless_check_results['c_note']}, your query returned no rows"


@points(1)
def test_2_4_a_clean(lossless_check_results):
    """lossless_check.sql returns no rows for your tables as built (only awarded if 2.4 b passes)"""
    got = _result(lossless_check_results, "a")
    b = _result(lossless_check_results, "b")
    assert len(b) >= 1, "only awarded when your query also catches a deleted row"
    assert len(got) == 0, f"your query returned {len(got)} rows for your tables as normalize.sql built them"
