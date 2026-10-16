"""
app_queries.py — Questions 2.1 and 2.2.   SUBMIT THIS FILE.

Fill in every function that raises NotImplementedError.  Do not rename the
functions, change their parameters, or change what they return: the
autograder calls them exactly as they are written here.

Every function receives an open connection, `conn`, and must use it for all
of its queries.  Do NOT open your own connection inside a function.

To try a function by hand:

    python3 -i app_queries.py
    >>> conn = get_connection()
    >>> get_top_songs(conn, "A0017", 5)

To run the public tests:

    python3 -m pytest tests/ -v
"""

from __future__ import annotations

from db import get_connection  # noqa: F401  (handy for trying things by hand)


# =============================================================================
# 2.1 — Database-backed application functions                     (20 points)
# =============================================================================

def get_top_songs(conn, artist_id: str, k: int) -> list[tuple[str, str, int]]:
    """Return the k most-played tracks by one artist.

    Each result is a tuple  (track_id, title, play_count).

      * A track is "by" an artist if it is on one of that artist's albums.
      * play_count is the number of rows in `play` for that track.  Tracks the
        artist has released that were NEVER played still count, with
        play_count 0.
      * Order by play_count, highest first; break ties by track_id, A to Z.
      * Return at most k tuples (fewer if the artist has fewer tracks).
      * An artist_id with no tracks returns [].

    Example (made-up values):
        >>> get_top_songs(conn, "A0001", 2)
        [('T00012', 'Long Harbor', 31), ('T00009', 'Ashfall', 27)]
    """
    raise NotImplementedError


def create_playlist(conn, listener_id: str, name: str, track_ids: list[str]) -> int:
    """Create a playlist for a listener and return its new playlist_id.

      * Insert one row into `playlist` (created_date is today: use CURDATE()),
        and one row into `playlist_track` per track, with position 1, 2, 3, ...
        in the order the track_ids are given.  An empty track_ids list makes
        an empty playlist.
      * Do not choose the playlist_id yourself: MySQL assigns it
        (AUTO_INCREMENT).  After the INSERT, `cursor.lastrowid` holds it.
      * On success, COMMIT, then return the new playlist_id.

    All or nothing.  If ANYTHING is wrong — the listener does not exist, a
    track does not exist, or the same track appears twice — then:
      * raise ValueError, and
      * leave the database exactly as it was: no playlist row and no
        playlist_track rows may survive, not even the ones inserted before the
        problem was found.  (See "Commit and rollback" in the handout.)

    Example:
        >>> create_playlist(conn, "L0001", "Road Trip 2", ["T00012", "T00009"])
        715
    """
    raise NotImplementedError


def search_songs(conn, text: str) -> list[tuple[str, str, str]]:
    """Search track titles.  `text` is whatever a user typed into a search box.

    Each result is a tuple  (track_id, title, artist_name).

      * Return every track whose title CONTAINS `text` anywhere, ignoring
        case ("harbor" matches "Long Harbor" and "HARBOR LIGHTS").
      * Order by track_id, A to Z.
      * You do not need to treat % or _ in `text` specially.

    `text` comes straight from a user, so it can contain anything at all —
    quotes, SQL keywords, the inputs from question 1.2.  Whatever it contains,
    this function must only ever search titles.  Use a parameterized query.

    Example:
        >>> search_songs(conn, "sailor's")
        [('T06664', "Sailor's Night", "Nora O'Connell")]
    """
    raise NotImplementedError


# =============================================================================
# 2.2 — Speed up the dashboard                                   (10 points)
# =============================================================================

def get_dashboard_slow(conn, listener_id: str) -> list[tuple[int, str, int, int]]:
    """PROVIDED — works correctly, but has the N+1 problem.  Do not edit.

    Returns one tuple per playlist the listener owns:
        (playlist_id, name, num_tracks, total_duration_sec)
    ordered by playlist_id.  An empty playlist has num_tracks 0 and
    total_duration_sec 0.  A listener with no playlists gets [].
    """
    cur = conn.cursor()

    # 1 query for the list of playlists ...
    cur.execute(
        "SELECT playlist_id, name FROM playlist "
        "WHERE listener_id = %s ORDER BY playlist_id",
        (listener_id,),
    )
    playlists = cur.fetchall()

    # ... then 1 more query PER playlist.
    result = []
    for playlist_id, name in playlists:
        cur.execute(
            "SELECT COUNT(*), SUM(t.duration_sec) "
            "FROM playlist_track pt JOIN track t ON pt.track_id = t.track_id "
            "WHERE pt.playlist_id = %s",
            (playlist_id,),
        )
        num_tracks, total = cur.fetchone()
        result.append((playlist_id, name, int(num_tracks), int(total or 0)))

    cur.close()
    return result


def get_dashboard(conn, listener_id: str) -> list[tuple[int, str, int, int]]:
    """Return EXACTLY what get_dashboard_slow returns, for every listener, but
    using AT MOST 2 queries no matter how many playlists the listener has.

    Return plain Python ints for the two numbers (SUM() comes back from MySQL
    as a Decimal; wrap it in int()).

    Check yourself:
        >>> from db import QueryCounter
        >>> qc = QueryCounter(get_connection())
        >>> get_dashboard(qc, "L0001") == get_dashboard_slow(qc, "L0001")
        True
    and look at qc.queries to see what was sent.
    """
    raise NotImplementedError
