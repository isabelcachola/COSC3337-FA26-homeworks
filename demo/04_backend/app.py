"""Steps 4-5: a thin JSON API over the queries from step 3.

Run:  python 04_backend/app.py     ->  http://localhost:5000
Try:  curl localhost:5000/api/events
"""
import pymysql
from flask import Flask, jsonify, request

import db

# Step 5's front end lives in ../05_frontend and is served by this same process.
app = Flask(__name__, static_folder="../05_frontend", static_url_path="")


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/api/clubs")
def clubs():
    return jsonify(db.query("SELECT club_id, name FROM clubs ORDER BY name"))


@app.get("/api/members")
def members():
    return jsonify(db.query("SELECT member_id, name FROM members ORDER BY name"))


@app.get("/api/events")
def events():
    club = request.args.get("club", type=int)  # None when absent or not a number
    rows = db.query(
        """
        SELECT e.event_id, e.title, e.location, e.start_time,
               c.club_id, c.name AS club_name,
               COUNT(r.member_id) AS going_count
        FROM events e
        JOIN clubs c      ON c.club_id = e.club_id
        LEFT JOIN rsvps r ON r.event_id = e.event_id AND r.status = 'going'
        WHERE e.start_time >= NOW()
          AND (%s IS NULL OR c.club_id = %s)
        GROUP BY e.event_id, e.title, e.location, e.start_time, c.club_id, c.name
        ORDER BY e.start_time
        """,
        (club, club),
    )
    return jsonify(rows)


@app.get("/api/events/<int:event_id>")
def event_detail(event_id):
    events = db.query(
        """
        SELECT e.event_id, e.title, e.location, e.start_time, e.end_time,
               c.name AS club_name
        FROM events e JOIN clubs c ON c.club_id = e.club_id
        WHERE e.event_id = %s
        """,
        (event_id,),
    )
    if not events:
        return jsonify(error="event not found"), 404
    attendees = db.query(
        """
        SELECT m.member_id, m.name, r.status
        FROM rsvps r JOIN members m ON m.member_id = r.member_id
        WHERE r.event_id = %s
        ORDER BY r.rsvp_time
        """,
        (event_id,),
    )
    return jsonify({**events[0], "attendees": attendees})


@app.post("/api/rsvp")
def rsvp():
    body = request.get_json(silent=True) or {}
    member_id, event_id = body.get("member_id"), body.get("event_id")
    if not isinstance(member_id, int) or not isinstance(event_id, int):
        return jsonify(error="member_id and event_id (integers) are required"), 400
    db.execute(
        "INSERT INTO rsvps (member_id, event_id, status) VALUES (%s, %s, %s)",
        (member_id, event_id, body.get("status", "going")),
    )
    return jsonify(member_id=member_id, event_id=event_id), 201


# The database is the source of truth for integrity rules; the API just
# translates its errors into HTTP status codes.
@app.errorhandler(pymysql.err.IntegrityError)
def integrity_error(e):
    code = e.args[0]
    if code == 1062:  # duplicate primary key: already RSVPed
        return jsonify(error="already RSVPed to this event"), 409
    if code == 1452:  # foreign key: no such member or event
        return jsonify(error="member or event does not exist"), 404
    return jsonify(error="request violates a database constraint"), 400


@app.errorhandler(pymysql.err.DataError)
def data_error(e):  # e.g. a status that is not in the ENUM
    return jsonify(error="invalid value (status must be going, maybe or not_going)"), 400


if __name__ == "__main__":
    app.run(debug=True, port=5000)
