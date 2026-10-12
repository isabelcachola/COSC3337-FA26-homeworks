"""Step 2: fill the database with demo data.

Run:  python 02_seed/seed.py        (after running 01_schema/schema.sql)

A few rows are hand-written so the demo output is predictable (members 1-3
RSVP to event 1, etc.); the rest are generated with Faker. Faker is seeded,
so every run produces the same data.
"""
import getpass
import os
import random
from datetime import datetime, timedelta

import pymysql
from faker import Faker


def load_env():
    """Read demo/.env into os.environ (real environment variables win)."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ.setdefault(key.strip(), value.strip().strip("\"'"))
    except FileNotFoundError:
        pass


load_env()

random.seed(3337)
fake = Faker()
Faker.seed(3337)


def connect():
    return pymysql.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        port=int(os.environ.get("DB_PORT") or 3306),
        user=os.environ.get("DB_USER") or getpass.getuser(),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "club_events"),
        unix_socket=os.environ.get("DB_SOCKET") or None,
    )


CLUBS = [
    ("Chess Club", "Casual and ranked games, all levels welcome."),
    ("Robotics Society", "Build, program and battle small robots."),
    ("Film Society", "Weekly screenings and discussion."),
    ("Hiking Club", "Day hikes around the Houston area."),
    ("Data Science Club", "Workshops, datathons and guest talks."),
]

# Hand-written members: ids 1-4 are predictable for the demo.
FIXED_MEMBERS = [
    ("Ada Lovelace", "ada@example.edu"),
    ("Alan Turing", "alan@example.edu"),
    ("Grace Hopper", "grace@example.edu"),
    ("Katherine Johnson", "katherine@example.edu"),
]

TITLES = {
    1: ["Beginner Openings", "Blitz Tournament", "Endgame Study Night"],
    2: ["Build Night", "Robot Combat Showdown", "Intro to Arduino"],
    3: ["Sci-Fi Double Feature", "Short Film Night", "Director's Cut Discussion"],
    4: ["Sunrise Trail Hike", "Creek Cleanup Walk", "Gear Swap and Hike"],
    5: ["SQL Workshop", "Kaggle Study Group", "Guest Talk: Data in Industry"],
}
LOCATIONS = ["Room 101", "Science Hall 204", "Student Center", "Library Atrium", "Main Quad"]


def main():
    conn = connect()
    cur = conn.cursor()
    now = datetime.now().replace(minute=0, second=0, microsecond=0)

    cur.executemany("INSERT INTO clubs (name, description) VALUES (%s, %s)", CLUBS)

    members = list(FIXED_MEMBERS)
    for _ in range(36):
        members.append((fake.name(), fake.unique.email()))
    cur.executemany("INSERT INTO members (name, email) VALUES (%s, %s)", members)

    # Events 1-5: one upcoming event per club, hand-placed in the next few days.
    events = []
    for club_id in range(1, 6):
        start = now + timedelta(days=club_id, hours=18 - now.hour)
        events.append((club_id, TITLES[club_id][0], LOCATIONS[club_id - 1],
                       start, start + timedelta(hours=2)))
    # Plus generated events: mostly upcoming, a few already past.
    for _ in range(16):
        club_id = random.randint(1, 5)
        start = now + timedelta(days=random.randint(-14, 30), hours=random.randint(8, 20) - now.hour)
        events.append((club_id, random.choice(TITLES[club_id]), random.choice(LOCATIONS),
                       start, start + timedelta(hours=random.randint(1, 3))))
    cur.executemany(
        "INSERT INTO events (club_id, title, location, start_time, end_time)"
        " VALUES (%s, %s, %s, %s, %s)", events)

    # RSVPs. Hand-written first, so the demo can rely on them.
    rsvps = {
        (1, 1): "going", (2, 1): "going", (3, 1): "going",   # three going to event 1
        (1, 2): "going", (2, 3): "maybe",
    }
    for member_id in range(5, len(members) + 1):
        for event_id in random.sample(range(1, len(events) + 1), random.randint(0, 4)):
            rsvps[(member_id, event_id)] = random.choices(
                ["going", "maybe", "not_going"], weights=[6, 3, 1])[0]
    cur.executemany(
        "INSERT INTO rsvps (member_id, event_id, status) VALUES (%s, %s, %s)",
        [(m, e, s) for (m, e), s in rsvps.items()])

    conn.commit()
    for table in ("clubs", "members", "events", "rsvps"):
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        print(f"{table:8} {cur.fetchone()[0]} rows")
    conn.close()


if __name__ == "__main__":
    main()
