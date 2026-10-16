"""
Shared setup for the public tests.  You do not need to read or edit this.

Run the tests from the HW3 directory:

    python3 -m pytest tests/ -v              # everything
    python3 -m pytest tests/test_2_1_public.py -v
    python3 -m pytest tests/ -v -k search    # only tests with "search" in the name

Any playlist a test creates is deleted again afterwards, so running the tests
never changes your database.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HW_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HW_DIR))

from db import get_connection  # noqa: E402

PLAYS_CSV = HW_DIR / "data" / "plays.csv"


@pytest.fixture
def conn():
    """A fresh connection for one test.  Afterwards: undo anything uncommitted,
    and delete any playlists the test created."""
    c = get_connection()
    cur = c.cursor()
    cur.execute("SELECT COALESCE(MAX(playlist_id), 0) FROM playlist")
    (max_before,) = cur.fetchone()
    cur.close()
    c.commit()
    yield c
    try:
        c.rollback()
        c.close()
    except Exception:
        pass
    clean = get_connection()
    cur = clean.cursor()
    cur.execute("DELETE FROM playlist_track WHERE playlist_id > %s", (max_before,))
    cur.execute("DELETE FROM playlist WHERE playlist_id > %s", (max_before,))
    clean.commit()
    cur.close()
    clean.close()


def table_counts(c) -> tuple[int, int]:
    """(rows in playlist, rows in playlist_track), as seen by connection c."""
    cur = c.cursor()
    cur.execute("SELECT (SELECT COUNT(*) FROM playlist), (SELECT COUNT(*) FROM playlist_track)")
    row = cur.fetchone()
    cur.close()
    return int(row[0]), int(row[1])


def sql_rows(c, query: str) -> list[tuple]:
    cur = c.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    return rows


# The SQL each MapReduce job must agree with.
GENRE_SQL = """
    SELECT al.genre, COUNT(*)
    FROM play p
         JOIN track t  ON t.track_id = p.track_id
         JOIN album al ON al.album_id = t.album_id
    GROUP BY al.genre
"""

TOP_ARTIST_SQL = """
    WITH counts AS (
        SELECT p.listener_id, al.artist_id, COUNT(*) AS n
        FROM play p
             JOIN track t  ON t.track_id = p.track_id
             JOIN album al ON al.album_id = t.album_id
        GROUP BY p.listener_id, al.artist_id
    )
    SELECT listener_id, artist_id, n
    FROM (SELECT counts.*,
                 ROW_NUMBER() OVER (PARTITION BY listener_id
                                    ORDER BY n DESC, artist_id) AS rk
          FROM counts) ranked
    WHERE rk = 1
"""
