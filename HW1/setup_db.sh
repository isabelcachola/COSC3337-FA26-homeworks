#!/bin/bash
# ---------------------------------------------------------------------
# COSC 3337 — HW 1: load the databases and set up your MySQL access.
#
#     bash setup_db.sh
#
# Run this once, from the HW1 directory of the course repository.  Safe to run
# again at any time — it restores both databases to a clean, known-good state,
# which is your repair command if anything ever looks wrong.
#
# What it does, and why:
#
#   1. Loads both databases (soundwave and soundwave_small).
#
#   2. Makes sure you can reach them without a password.  MySQL authenticates
#      you through the operating system (auth_socket): because you are already
#      logged in to the VM, MySQL trusts you without asking for anything.  So
#      `mysql soundwave` just works — no -u, no -p, no prompt, nothing to
#      memorise or lose.
#
# You are root on this VM, so nothing prevents you from destroying the data.
# That is fine: re-running this script restores it in seconds.  Consider that
# your undo button rather than something to avoid needing.
#
# Options:
#   --as USERNAME    also grant read-only access to a non-root account
#                    (instructors provisioning a VM for someone else)
#   --skip-grant     only load the data, do not touch any MySQL account
# ---------------------------------------------------------------------

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

GRANTEE=""
SKIP_GRANT=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --as)         GRANTEE="${2:-}"; shift 2 ;;
    --skip-grant) SKIP_GRANT=1; shift ;;
    -h|--help)    sed -n '2,30p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *)            echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

# Work out who should get read-only access.
#
#   - normal user            -> that user
#   - sudo from a normal user -> the user behind the sudo, not root
#   - a real root login      -> nobody; root already has full access to MySQL
#                               through auth_socket, so there is nothing to
#                               create and no password to set
if [[ -z "$GRANTEE" ]]; then
  if [[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != "root" ]]; then
    GRANTEE="$SUDO_USER"
    echo "Note: running under sudo — granting access to '$GRANTEE', not to root."
  elif [[ "$(id -u)" -eq 0 ]]; then
    GRANTEE=""
  else
    GRANTEE="$(whoami)"
  fi
fi

# The .sql files live next to this script, so it works from any directory.
for f in soundwave.sql soundwave_small.sql; do
  if [[ ! -f "$HERE/$f" ]]; then
    echo "Cannot find $f next to this script (looked in $HERE)." >&2
    echo "Run this from the HW1 directory of the course repository." >&2
    exit 1
  fi
done

if ! command -v mysql >/dev/null 2>&1; then
  echo "The 'mysql' command was not found. Is this the right VM?" >&2
  exit 1
fi

# `sudo` is a harmless no-op when already root.
SUDO=""
[[ "$(id -u)" -ne 0 ]] && SUDO="sudo"

echo "Loading soundwave ..."
$SUDO mysql < "$HERE/soundwave.sql"
echo "Loading soundwave_small ..."
$SUDO mysql < "$HERE/soundwave_small.sql"

if [[ "$SKIP_GRANT" -eq 1 ]]; then
  echo "Skipping the grant, as asked."
elif [[ -z "$GRANTEE" ]]; then
  echo "You are root, so MySQL already lets you in through the socket —"
  echo "no account to create and no password to set."
else
  echo "Granting read-only access to '$GRANTEE' ..."
  $SUDO mysql <<SQL
CREATE USER IF NOT EXISTS '${GRANTEE}'@'localhost' IDENTIFIED WITH auth_socket;
GRANT SELECT ON soundwave.*       TO '${GRANTEE}'@'localhost';
GRANT SELECT ON soundwave_small.* TO '${GRANTEE}'@'localhost';
FLUSH PRIVILEGES;
SQL
fi

echo
echo "Checking the data loaded ..."
$SUDO mysql -t -e "SELECT 'artist' AS t, COUNT(*) AS n FROM soundwave.artist
                   UNION ALL SELECT 'album', COUNT(*) FROM soundwave.album
                   UNION ALL SELECT 'track', COUNT(*) FROM soundwave.track;"

echo
if [[ -n "$GRANTEE" ]]; then
  echo "Done. $GRANTEE can now connect with:   mysql soundwave"
  echo "                                   or  mysql soundwave_small"
  echo "No password needed, and that account is read-only."
else
  echo "Done. Connect with:   mysql soundwave"
  echo "                  or  mysql soundwave_small"
  echo
  echo "If you ever damage the data, re-run this script to restore it."
fi
