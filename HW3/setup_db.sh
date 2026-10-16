#!/bin/bash
# ---------------------------------------------------------------------
# COSC 3337 — HW 3: load the soundwave_app database and the Python packages.
#
#     bash setup_db.sh
#
# Run this once, from the HW3 directory of the course repository.  Safe to run
# again at any time — it restores soundwave_app to a clean, known-good state,
# which is your repair command if anything ever looks wrong with the data.
#
# What it does:
#
#   1. Loads soundwave_app: the HW 1 catalog (artist, album, track) plus the
#      application tables (listener, playlist, playlist_track, play).
#
#   2. Installs the two Python packages the starter code needs, if they are
#      missing: the MySQL connector and pytest.
#
# Unlike HW 1, your code for this assignment WRITES to the database
# (create_playlist inserts rows), so access to soundwave_app is read-write.
# Nothing you do can harm the HW 1 databases.
# ---------------------------------------------------------------------

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -f "$HERE/soundwave_app.sql" ]]; then
  echo "Cannot find soundwave_app.sql next to this script (looked in $HERE)." >&2
  echo "Run this from the HW3 directory of the course repository." >&2
  exit 1
fi

if ! command -v mysql >/dev/null 2>&1; then
  echo "The 'mysql' command was not found. Is this the right VM?" >&2
  exit 1
fi

IS_ROOT=0
[[ "$(id -u)" -eq 0 ]] && IS_ROOT=1

# How to run mysql with enough privileges to (re)create soundwave_app.
# Try plain `mysql` first: as root on the course VM it logs in through the
# socket with no password.  Fall back to `sudo mysql` only when that fails.
# `-e` with no -p never prompts: a refusal fails immediately instead.
MYSQL=(mysql)
if ! PROBE="$(mysql -e "CREATE DATABASE IF NOT EXISTS soundwave_app" </dev/null 2>&1)"; then
  if [[ "$PROBE" == *"Can't connect"* ]]; then
    echo "Could not reach MySQL:" >&2
    echo "    $PROBE" >&2
    echo "If MySQL is not running, start it with   service mysql start" >&2
    echo "(prefix with sudo if you are not root), then re-run this script." >&2
    exit 1
  elif [[ "$IS_ROOT" -eq 1 ]]; then
    echo "MySQL refused to let root in without a password." >&2
    echo "On the course VM root needs no password; if you changed that, run" >&2
    echo "    mysql -u root -p < soundwave_app.sql" >&2
    echo "and then re-run this script.  Otherwise, email me." >&2
    exit 1
  fi
  echo "Your account cannot create databases in MySQL, so this step uses sudo."
  echo "If it asks for a password, it is your VM login password, not a MySQL one."
  MYSQL=(sudo mysql)
fi

echo "Loading soundwave_app (about 10 seconds) ..."
"${MYSQL[@]}" < "$HERE/soundwave_app.sql"

# A non-root login needs its own (read-write) account on soundwave_app.
GRANTEE=""
if [[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != "root" ]]; then
  GRANTEE="$SUDO_USER"
elif [[ "$IS_ROOT" -eq 0 && "${MYSQL[0]}" == "sudo" ]]; then
  GRANTEE="$(whoami)"      # (if plain mysql worked, this account already has access)
fi
if [[ -n "$GRANTEE" ]]; then
  echo "Granting read-write access on soundwave_app to '$GRANTEE' ..."
  "${MYSQL[@]}" <<SQL
CREATE USER IF NOT EXISTS '${GRANTEE}'@'localhost' IDENTIFIED WITH auth_socket;
GRANT SELECT, INSERT, UPDATE, DELETE ON soundwave_app.* TO '${GRANTEE}'@'localhost';
FLUSH PRIVILEGES;
SQL
  echo "NOTE: you are not logged in as root, so before running Python, do:"
  echo "      export DB_USER=$GRANTEE"
fi

# Python packages.  root installs the Ubuntu packages; anyone else installs
# them for their own account with pip, which needs no password.
if python3 -c "import mysql.connector, pytest" 2>/dev/null; then
  echo "Python packages already installed."
elif [[ "$IS_ROOT" -eq 1 ]]; then
  echo "Installing the MySQL connector and pytest for Python ..."
  DEBIAN_FRONTEND=noninteractive apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq python3-mysql.connector python3-pytest
else
  echo "Installing the MySQL connector and pytest for your account ..."
  python3 -m pip install --user -q --break-system-packages mysql-connector-python pytest 2>/dev/null \
    || python3 -m pip install --user -q mysql-connector-python pytest
fi

echo
echo "Checking the data loaded ..."
"${MYSQL[@]}" -t -e "SELECT 'track' AS t, COUNT(*) AS n FROM soundwave_app.track
                   UNION ALL SELECT 'listener', COUNT(*) FROM soundwave_app.listener
                   UNION ALL SELECT 'playlist', COUNT(*) FROM soundwave_app.playlist
                   UNION ALL SELECT 'play',     COUNT(*) FROM soundwave_app.play;"

echo "Checking Python can connect ..."
cd "$HERE"
# Connect Python as the same MySQL account that `mysql` used above.
if [[ -z "${DB_USER:-}" && "$IS_ROOT" -eq 0 ]]; then
  if [[ "${MYSQL[0]}" == "sudo" ]]; then
    export DB_USER="$(whoami)"
  else
    export DB_USER="$(mysql -N -e 'SELECT SUBSTRING_INDEX(CURRENT_USER(), "@", 1)' </dev/null)"
  fi
fi
python3 -c "
from db import get_connection
c = get_connection(); cur = c.cursor()
cur.execute('SELECT COUNT(*) FROM listener')
print('  Python connected: %d listeners' % cur.fetchone()[0])
"

echo
echo "Done. Connect with:   mysql soundwave_app"
echo "If you ever damage the data, re-run this script to restore it."
