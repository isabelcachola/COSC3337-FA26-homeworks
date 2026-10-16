"""
Public tests for 2.2.  get_dashboard must return exactly what
get_dashboard_slow returns, in at most 2 queries.
"""

import pytest

from app_queries import get_dashboard, get_dashboard_slow
from db import QueryCounter


@pytest.mark.parametrize("listener_id", [
    "L0001",   # five playlists
    "L0006",   # no playlists at all
    "L0007",   # owns an empty playlist
])
def test_dashboard_matches_slow(conn, listener_id):
    assert get_dashboard(conn, listener_id) == get_dashboard_slow(conn, listener_id)


def test_dashboard_query_count(conn):
    qc = QueryCounter(conn)
    get_dashboard(qc, "L0001")
    assert qc.count <= 2, (
        f"get_dashboard used {qc.count} queries; at most 2 allowed.\n"
        "Queries sent:\n  " + "\n  ".join(q.strip().split("\n")[0] for q in qc.queries)
    )
