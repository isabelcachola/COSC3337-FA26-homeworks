# Build a database-driven app: club event tracker

In this demo you build a small web app from the database up:

1. **Database:** a MySQL schema with keys and constraints, loaded with sample data.
2. **Queries:** the SQL the app needs, tested in the `mysql` shell.
3. **Backend:** a Flask API that runs those queries and returns JSON.
4. **Front end:** a plain HTML/JS page that calls the API.

The app tracks **clubs** that host **events**, and **members** who RSVP to events. Start by opening [`slides/system_design.html`](slides/system_design.html) in a browser for the big picture: how the three tiers connect and what each one does.

```
clubs 1───* events *───* members      (events–members is many-to-many, through the rsvps table)
```

This is a small model of what your final project needs: a database, an app that queries it with parameterized SQL, and a front end.

## Prerequisites

- **MySQL 8.0.16 or newer** (older versions silently ignore `CHECK` constraints), and a MySQL account that can `CREATE DATABASE`. The demo is set up for the MySQL `root` user, which already has every privilege. Run `./check_permissions.sh` to confirm your connection works before you start.
- **Python 3.9+**
- A terminal and a browser.

Work from the `demo/` folder:

```bash
cd demo
```

## Setup

Create a Python environment and install the libraries (Flask, PyMySQL, Faker):

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Tell the scripts how to reach MySQL. If your MySQL needs no password for your user (as on the course VM), skip this. Otherwise:

```bash
cp .env.example .env     # then edit .env: set DB_USER and DB_PASSWORD
```

The Python scripts read `.env`, but the `mysql` command-line client does not: by default it connects as your OS username with no password. If your MySQL needs a different user or password, either add `-u youruser -p` to every `mysql` command below, or put your login in `~/.my.cnf` once so plain `mysql` works:

```ini
[client]
user=root
password=YOUR_PASSWORD
```

```bash
chmod 600 ~/.my.cnf
```

> **Start over any time:** `./reset_db.sh` drops the demo database and all its tables (it asks first). Add `--rebuild` to also re-run Steps 1–2 for you.
>
> **Want to skip ahead?** `./run_demo.sh` runs Steps 1–5 in one go. Do the steps by hand first, so you see what each does.

## Step 1: Create the schema

Read [`01_schema/schema.sql`](01_schema/schema.sql). Notice:
- Every table has a primary key.
- `events.club_id` is a foreign key to `clubs`.
- `CHECK (end_time > start_time)` and the `ENUM` on `rsvps.status` reject bad data.
- `rsvps` has a **composite primary key** `(member_id, event_id)`, so no one can RSVP twice to the same event.

```bash
mysql < 01_schema/schema.sql
mysql club_events -e "SHOW TABLES; DESCRIBE events;"
```

You should see four tables: `clubs`, `events`, `members`, `rsvps`. Re-running the first command wipes and rebuilds the database, so it's safe to repeat.

## Step 2: Load sample data

[`02_seed/seed.py`](02_seed/seed.py) inserts a few hand-written rows, so everyone sees the same output, plus generated ones from Faker.

```bash
.venv/bin/python 02_seed/seed.py
```

It prints the number of rows in each table (5 clubs, 40 members, 21 events, and some RSVPs). Look at the data:

```bash
mysql club_events -e "SELECT * FROM events LIMIT 5;"
```

**Try breaking the rules.** Run the statements in [`01_schema/constraint_demo.sql`](01_schema/constraint_demo.sql) one at a time in the `mysql` shell (run `mysql club_events` to open it). Each should fail. For each, say which constraint stopped it and why.

## Step 3: Write the queries

Open [`03_queries/queries.sql`](03_queries/queries.sql). It has the five queries the app needs. Run them all:

```bash
mysql club_events < 03_queries/queries.sql
```

(Q4 inserts one RSVP. Run the file twice and the second insert fails with a duplicate-key error, which is the composite primary key at work.)

Things to notice in Q1:
- `LEFT JOIN rsvps` keeps events that nobody has RSVPed to yet (count 0). Change it to a plain `JOIN` and see what disappears.
- `GROUP BY` plus `COUNT` gives the attendee count per event.
- The `@club` variable stands in for a value the app will pass later. Change `SET @club = NULL;` to `SET @club = 2;` and re-run.

## Step 4: Start the backend API

[`04_backend/app.py`](04_backend/app.py) is a thin Flask wrapper around the Step 3 queries. [`04_backend/db.py`](04_backend/db.py) holds the connection helpers.

Things to notice:
- Every query uses `%s` placeholders and passes values separately. The driver escapes them, and this is what protects you from SQL injection. **Never build SQL by gluing strings together.**
- The API doesn't re-check every rule. It lets the database enforce them and turns the database's errors into HTTP codes (duplicate → 409, missing foreign key → 404).

Start the server:

```bash
.venv/bin/python 04_backend/app.py
```

In a second terminal, test it with `curl`:

```bash
curl localhost:5000/api/events
curl "localhost:5000/api/events?club=2"
curl localhost:5000/api/events/1
curl -X POST localhost:5000/api/rsvp -H 'Content-Type: application/json' \
     -d '{"member_id": 4, "event_id": 2}'
```

Run the last command a second time. You should get `409 already RSVPed to this event`. (If you ran Step 3's Q4, member 4 already RSVPed to event 1, so try event 2 as shown.)

| Route | What it does |
|---|---|
| `GET /api/clubs` | list clubs |
| `GET /api/members` | list members |
| `GET /api/events?club=<id>` | upcoming events with going-counts, optionally for one club |
| `GET /api/events/<id>` | one event with its attendees |
| `POST /api/rsvp` | create an RSVP (`member_id`, `event_id`, optional `status`) |

## Step 5: Use the front end

With the server still running, open <http://localhost:5000>. Flask serves the files in [`05_frontend/`](05_frontend/), so there's nothing else to start.

Pick a member, click **RSVP** (the count goes up), click it again (you see the 409 error message), and filter by club. Then read [`05_frontend/app.js`](05_frontend/app.js): the page only calls the API with `fetch()`. It never sees SQL.

Go back to the slide and trace one RSVP click through all three tiers.

## Check yourself

- Why is the `rsvps` junction table needed, instead of a column on `events`?
- Where is the "no double RSVP" rule enforced, and why is that better than checking in Python?
- What would go wrong if `/api/events` built its SQL with an f-string and `?club=` came from the user?
- What changes if you add a `capacity` column to `events`? Which files do you touch?

## Extensions to try

1. Add an `/api/members/<id>/rsvps` route that uses query Q3.
2. Add a "cancel RSVP" button (`DELETE`).
3. Add a `capacity` column and refuse RSVPs when an event is full. Think about what happens if two people RSVP at the same time.
4. Show who is going when you click an event.

## Troubleshooting

| Problem | Likely cause and fix |
|---|---|
| `Access denied` from `mysql` or Python | For `mysql`: it doesn't read `.env`, so pass `-u`/`-p` or set up `~/.my.cnf` (see Setup). For Python: a wrong `DB_USER` or `DB_PASSWORD` in `.env`. Run `./check_permissions.sh` to test the `.env` login. |
| `Can't connect to MySQL server` | MySQL isn't running, or it's on a socket. Start it, or set `DB_SOCKET` in `.env`. |
| `Unknown database 'club_events'` | Run Step 1 first. |
| `Duplicate entry` when seeding | You ran the seed twice. Run `./reset_db.sh --rebuild`, or re-run Steps 1–2 by hand. |
| `ModuleNotFoundError` | Use `.venv/bin/python`, not `python3`, or activate the venv. |
| Port 5000 already in use | Another app owns the port (on macOS, AirPlay Receiver). Stop it, or change the port in `app.py`. |
| Event list is empty | Seed events are dated relative to when you seeded. If you seeded days ago they may be in the past. Re-run Steps 1–2. |

## Layout

```
demo/
├── README.md  LECTURE_NOTES.md  .env.example  requirements.txt  run_demo.sh  reset_db.sh  check_permissions.sh
├── slides/system_design.html      the system design slide
├── 01_schema/    schema.sql, constraint_demo.sql
├── 02_seed/      seed.py
├── 03_queries/   queries.sql
├── 04_backend/   app.py, db.py
└── 05_frontend/  index.html, app.js, style.css
```
