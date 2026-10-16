"""
Public tests for 2.1.  Passing these means your functions have the right shape
and handle the basic cases.  The autograder runs more tests than these, on a
different copy of the data, so also test your own edge cases.
"""

import pytest

from app_queries import create_playlist, get_top_songs, search_songs
from conftest import table_counts


# ---- get_top_songs -----------------------------------------------------------

def test_top_songs_basic(conn):
    assert get_top_songs(conn, "A0017", 5) == [
        ("T00498", "Highlife", 6),
        ("T00512", "Iron Shore", 6),
        ("T00519", "Migration", 6),
        ("T00500", "Salt Fathom", 5),
        ("T00505", "Marble Junction", 5),
    ]


def test_top_songs_never_played(conn):
    # A0201 has four tracks and nobody has ever played any of them.
    assert get_top_songs(conn, "A0201", 10) == [
        ("T06661", "Don't Wake the Harbor", 0),
        ("T06662", "Rock 'n' Roll Lullaby", 0),
        ("T06663", "O'er the Low Fields", 0),
        ("T06664", "Sailor's Night", 0),
    ]


# ---- create_playlist ---------------------------------------------------------

def test_create_playlist_valid(conn):
    before = table_counts(conn)
    new_id = create_playlist(conn, "L0006", "Test Mix", ["T00001", "T00002", "T00003"])
    assert isinstance(new_id, int)
    assert table_counts(conn) == (before[0] + 1, before[1] + 3)

    cur = conn.cursor()
    cur.execute("SELECT track_id, position FROM playlist_track "
                "WHERE playlist_id = %s ORDER BY position", (new_id,))
    assert cur.fetchall() == [("T00001", 1), ("T00002", 2), ("T00003", 3)]
    cur.close()


def test_create_playlist_bad_track_leaves_nothing(conn):
    before = table_counts(conn)
    with pytest.raises(ValueError):
        create_playlist(conn, "L0006", "Broken Mix", ["T00001", "T00002", "NOPE"])
    # Nothing may remain — not even the playlist row or the first two tracks.
    assert table_counts(conn) == before


# ---- search_songs ------------------------------------------------------------

def test_search_basic(conn):
    result = search_songs(conn, "harbor")
    assert len(result) == 89
    assert result[:3] == [
        ("T00052", "Vacant Harbor", "Meadow & Vault"),
        ("T00106", "Simple Harbor", "Freya Harlow"),
        ("T00151", "Vacant Harbor", "Diego Reyes"),
    ]


def test_search_apostrophe(conn):
    assert search_songs(conn, "sailor's") == [("T06664", "Sailor's Night", "Nora O'Connell")]


def test_search_injection_or(conn):
    # The input from question 1.2(b).  No title contains this text.
    assert search_songs(conn, "' OR '1'='1") == []
