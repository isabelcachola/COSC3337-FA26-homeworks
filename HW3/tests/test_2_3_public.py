"""
Public tests for 2.3.  The end-to-end tests check your MapReduce answers
against the same question asked in SQL, on the same data.
"""

import pytest

from conftest import GENRE_SQL, PLAYS_CSV, TOP_ARTIST_SQL, sql_rows
from mapreduce_driver import read_plays, run_mapreduce
from mapreduce_jobs import (count_map, count_reduce, genre_map, genre_reduce,
                            top_artist_job, top_map, top_reduce)

RECORD = {"play_id": "7", "listener_id": "L0001", "track_id": "T00012",
          "artist_id": "A0042", "genre": "Folk", "played_at": "2026-01-01 00:03:12"}


@pytest.fixture(scope="module")
def plays():
    return read_plays(str(PLAYS_CSV))


# ---- Job 1 -------------------------------------------------------------------

def test_genre_map():
    assert list(genre_map(RECORD)) == [("Folk", 1)]


def test_genre_reduce():
    assert genre_reduce("Folk", [1, 1, 1]) == ("Folk", 3)


def test_genre_matches_sql(conn, plays):
    expected = sorted((g, int(n)) for g, n in sql_rows(conn, GENRE_SQL))
    assert sorted(run_mapreduce(plays, genre_map, genre_reduce)) == expected


# ---- Job 2 -------------------------------------------------------------------

def test_count_map():
    assert list(count_map(RECORD)) == [(("L0001", "A0042"), 1)]


def test_top_map():
    assert list(top_map((("L0001", "A0042"), 17))) == [("L0001", ("A0042", 17))]


def test_top_reduce_tie():
    values = [("A0042", 17), ("A0007", 17), ("A0099", 3)]
    assert top_reduce("L0001", values) == ("L0001", ("A0007", 17))


def test_top_artist_matches_sql(conn, plays):
    expected = sorted((l, (a, int(n))) for l, a, n in sql_rows(conn, TOP_ARTIST_SQL))
    assert sorted(top_artist_job(plays)) == expected
