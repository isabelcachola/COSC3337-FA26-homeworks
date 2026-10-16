"""
mapreduce_jobs.py — Question 2.3.   SUBMIT THIS FILE.

Write the map and reduce functions for two MapReduce jobs over the play log.
The provided driver (mapreduce_driver.py) runs them: it calls your mapper on
every record, does the shuffle, and calls your reducer once per key.

RULES (the autograder checks them):
  * Do not import pandas, numpy, sqlite3, mysql, pymysql or collections.
  * Do not group values by key yourself — that is the shuffle's job.
  * A mapper only ever sees ONE record.  A reducer only ever sees ONE key and
    the list of values for that key.  Neither may read files or global state.

Each play record is a dict of strings (see read_plays in mapreduce_driver.py):

    {"play_id": "1", "listener_id": "L0042", "track_id": "T01234",
     "artist_id": "A0017", "genre": "Indie", "played_at": "2026-01-01 00:03:12"}

Try your jobs by hand:

    python3 -i mapreduce_jobs.py
    >>> plays = read_plays("data/plays.csv")
    >>> run_mapreduce(plays, genre_map, genre_reduce)[:3]
"""

from __future__ import annotations

from mapreduce_driver import read_plays, run_mapreduce  # noqa: F401


# =============================================================================
# Job 1 — plays per genre                                        (8 points)
#
# Final output: one (genre, number_of_plays) pair per genre, e.g.
#     [("Afrobeat", 1203), ("Classical", 877), ...]
#
# Example on three records:
#     genre_map({"genre": "Folk", ...})          -> [("Folk", 1)]
#     genre_reduce("Folk", [1, 1])               -> ("Folk", 2)
# =============================================================================

def genre_map(record: dict) -> list[tuple]:
    raise NotImplementedError


def genre_reduce(key, values: list) -> tuple:
    raise NotImplementedError


# =============================================================================
# Job 2 — each listener's most-played artist                    (10 points)
#
# Final output: one (listener_id, (artist_id, play_count)) pair per listener
# who has played anything, e.g.
#     [("L0001", ("A0042", 17)), ("L0002", ("A0153", 9)), ...]
# If a listener played two artists equally often, choose the SMALLER artist_id.
#
# One MapReduce stage cannot do this, because counting needs one grouping and
# choosing the maximum needs a different one.  So it takes two stages:
#
#   Stage 1 — count plays per (listener, artist) pair.
#       count_map(record)            -> [((listener_id, artist_id), 1)]
#       count_reduce(key, values)    -> ((listener_id, artist_id), count)
#
#   Stage 2 — for each listener, keep the artist with the highest count.
#       Stage 2's input records are Stage 1's OUTPUT pairs, i.e. each record
#       looks like  (("L0001", "A0042"), 17).
#       top_map(record)              -> [(listener_id, (artist_id, count))]
#       top_reduce(key, values)      -> (listener_id, (artist_id, count))
#
# Example:
#     count_map({"listener_id": "L0001", "artist_id": "A0042", ...})
#                                    -> [(("L0001", "A0042"), 1)]
#     top_map((("L0001", "A0042"), 17))
#                                    -> [("L0001", ("A0042", 17))]
#     top_reduce("L0001", [("A0042", 17), ("A0007", 17), ("A0099", 3)])
#                                    -> ("L0001", ("A0007", 17))
# =============================================================================

def count_map(record: dict) -> list[tuple]:
    raise NotImplementedError


def count_reduce(key, values: list) -> tuple:
    raise NotImplementedError


def top_map(record: tuple) -> list[tuple]:
    raise NotImplementedError


def top_reduce(key, values: list) -> tuple:
    raise NotImplementedError


def top_artist_job(records: list[dict]) -> list[tuple]:
    """Run Stage 1, then feed its output into Stage 2, and return Stage 2's
    output.  This is two calls to run_mapreduce."""
    raise NotImplementedError
