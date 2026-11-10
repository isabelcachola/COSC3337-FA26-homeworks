#!/bin/bash
# ---------------------------------------------------------------------
# COSC 3337 — HW 4: load the soundwave_live database and the Python packages.
#
#     bash setup_db.sh
#
# Run this once, from the HW4 directory of the course repository.  Safe to run
# again at any time — it restores soundwave_live to the original export, which
# is your repair command if anything ever looks wrong with the data.  It also
# DELETES any tables you created in soundwave_live, so re-run your scripts
# afterwards.
#
# What it does:
#
#   1. Loads soundwave_live: one table, ticket_sale_wide, the export of
#      Soundwave Live's ticket spreadsheet.
#
#   2. Installs the two Python packages the tests need, if they are missing:
#      the MySQL connector and pytest.  (Your answers are SQL; Python only
#      runs the tests.)
#
# In this homework you create, change and drop tables, so you get full
# access to soundwave_live.  Nothing you do can harm the other databases.
# ---------------------------------------------------------------------

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -f "$HERE/soundwave_live.sql" ]]; then
  echo "Cannot find soundwave_live.sql next to this script (looked in $HERE)." >&2
  echo "Run this from the HW4 directory of the course repository." >&2
  exit 1
fi

if ! command -v mysql >/dev/null 2>&1; then
  echo "The 'mysql' command was not found. Is this the right VM?" >&2
  exit 1
fi

IS_ROOT=0
[[ "$(id -u)" -eq 0 ]] && IS_ROOT=1

# How to run mysql with enough privileges to (re)create soundwave_live.
# Try plain `mysql` first: as root on the course VM it logs in through the
# socket with no password.  Fall back to `sudo mysql` only when that fails.
# `-e` with no -p never prompts: a refusal fails immediately instead.
MYSQL=(mysql)
if ! PROBE="$(mysql -e "CREATE DATABASE IF NOT EXISTS soundwave_live" </dev/null 2>&1)"; then
  if [[ "$PROBE" == *"Can't connect"* ]]; then
    echo "Could not reach MySQL:" >&2
    echo "    $PROBE" >&2
    echo "If MySQL is not running, start it with   service mysql start" >&2
    echo "(prefix with sudo if you are not root), then re-run this script." >&2
    exit 1
  elif [[ "$IS_ROOT" -eq 1 ]]; then
    echo "MySQL refused to let root in without a password." >&2
    echo "On the course VM root needs no password; if you changed that, run" >&2
    echo "    mysql -u root -p < soundwave_live.sql" >&2
    echo "and then re-run this script.  Otherwise, email me." >&2
    exit 1
  fi
  echo "Your account cannot create databases in MySQL, so this step uses sudo."
  echo "If it asks for a password, it is your VM login password, not a MySQL one."
  MYSQL=(sudo mysql)
fi

echo "Loading soundwave_live ..."
"${MYSQL[@]}" < "$HERE/soundwave_live.sql"

# A non-root login needs its own (read-write) account on soundwave_live.
GRANTEE=""
if [[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != "root" ]]; then
  GRANTEE="$SUDO_USER"
elif [[ "$IS_ROOT" -eq 0 && "${MYSQL[0]}" == "sudo" ]]; then
  GRANTEE="$(whoami)"      # (if plain mysql worked, this account already has access)
fi
if [[ -n "$GRANTEE" ]]; then
  echo "Granting full access to soundwave_live to '$GRANTEE' ..."
  "${MYSQL[@]}" <<SQL
CREATE USER IF NOT EXISTS '${GRANTEE}'@'localhost' IDENTIFIED WITH auth_socket;
GRANT ALL PRIVILEGES ON soundwave_live.* TO '${GRANTEE}'@'localhost';
FLUSH PRIVILEGES;
SQL
  echo "NOTE: you are not logged in as root.  If you run the tests with sudo, or as"
  echo "      another user, first do:   export DB_USER=$GRANTEE"
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
"${MYSQL[@]}" -t -e "SELECT COUNT(*) AS rows_in_ticket_sale_wide,
                            COUNT(DISTINCT order_id) AS orders
                     FROM soundwave_live.ticket_sale_wide;"

echo "Checking Python can connect ..."
cd "$HERE"
python3 -c "
import sys; sys.path.insert(0, 'tests')
import hw4lib as H
print('  Python connected as %s: %d rows' % (H._user(), H.rows('SELECT COUNT(*) FROM ticket_sale_wide')[0][0]))
"

echo
echo "Done. Connect with:   mysql soundwave_live"
echo "If you ever damage the data, re-run this script to restore it."
