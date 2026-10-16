"""
mapreduce_driver.py — PROVIDED.  Do not edit, and do not submit.

A tiny, single-machine MapReduce.  It does the parts a framework like Hadoop
or Spark does for you:

    1. MAP      call map_fn(record) on every input record; each call returns
                a list of (key, value) pairs
    2. SHUFFLE  group every value by its key:  key -> [value, value, ...]
    3. REDUCE   call reduce_fn(key, values) once per key; each call returns
                ONE (key, result) pair

You write map_fn and reduce_fn (in mapreduce_jobs.py).  You never write the
shuffle — that is the whole point of the framework.

    from mapreduce_driver import run_mapreduce, read_plays

    plays = read_plays("data/plays.csv")
    output = run_mapreduce(plays, genre_map, genre_reduce)
"""

from __future__ import annotations

import csv
from typing import Any, Callable, Iterable

Pair = tuple[Any, Any]


def read_plays(path: str = "data/plays.csv") -> list[dict]:
    """Read the play log.  Each record is a dict with string values:

        {"play_id": "1", "listener_id": "L0042", "track_id": "T01234",
         "artist_id": "A0017", "genre": "Indie", "played_at": "2026-01-01 00:03:12"}
    """
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def run_mapreduce(records: Iterable[Any],
                  map_fn: Callable[[Any], list[Pair]],
                  reduce_fn: Callable[[Any, list[Any]], Pair]) -> list[Pair]:
    """Run one MapReduce job and return the reducer outputs, sorted by key.

    The output is a list of (key, result) pairs, so it can be fed straight
    into another run_mapreduce call as the input records of a second stage.
    """
    # 1. MAP
    groups: dict[Any, list[Any]] = {}
    for record in records:
        pairs = map_fn(record)
        if pairs is None:
            raise TypeError("map_fn returned None — it must return a list of (key, value) pairs")
        for pair in pairs:
            if not (isinstance(pair, tuple) and len(pair) == 2):
                raise TypeError(f"map_fn must return (key, value) pairs, got {pair!r}")
            key, value = pair
            # 2. SHUFFLE: group values by key
            groups.setdefault(key, []).append(value)

    # 3. REDUCE, one call per key, in key order
    output = []
    for key in sorted(groups):
        result = reduce_fn(key, groups[key])
        if not (isinstance(result, tuple) and len(result) == 2):
            raise TypeError(f"reduce_fn must return one (key, result) pair, got {result!r}")
        output.append(result)
    return output
