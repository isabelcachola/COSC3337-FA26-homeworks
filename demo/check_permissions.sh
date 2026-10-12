#!/usr/bin/env bash
# Check that MySQL root can run the demo. Nothing needs granting: root already has
# all privileges. This creates and drops a scratch database to prove it.
#   ./check_permissions.sh        (on the course VM: sudo ./check_permissions.sh)
# Connects as DB_USER from .env, or root if that's unset.
set -euo pipefail
cd "$(dirname "$0")"

if [[ -f .env ]]; then set -a; source .env; set +a; fi

MYSQL=(mysql -u "${DB_USER:-root}")
[[ -n "${DB_HOST:-}"   ]] && MYSQL+=(-h "$DB_HOST")
[[ -n "${DB_PORT:-}"   ]] && MYSQL+=(-P "$DB_PORT")
[[ -n "${DB_SOCKET:-}" ]] && MYSQL+=(--socket "$DB_SOCKET")
[[ -n "${DB_PASSWORD:-}" ]] && export MYSQL_PWD="$DB_PASSWORD"   # keeps it out of `ps`

SCRATCH=club_events_permcheck
cleanup() { "${MYSQL[@]}" -e "DROP DATABASE IF EXISTS $SCRATCH" 2>/dev/null || true; }
trap cleanup EXIT

if ! VERSION="$("${MYSQL[@]}" -N -e "SELECT VERSION()" 2>&1)"; then
  echo "FAIL: cannot connect as '${DB_USER:-root}':" >&2
  echo "  $VERSION" >&2
  echo "Check DB_USER / DB_PASSWORD in .env, or run with sudo if root uses the socket." >&2
  exit 1
fi
echo "Connected as '${DB_USER:-root}' to MySQL $VERSION"

# Everything the demo does: Step 1 create/drop, Step 2 insert, Step 3 select.
if ! "${MYSQL[@]}" <<SQL
DROP DATABASE IF EXISTS $SCRATCH;
CREATE DATABASE $SCRATCH;
USE $SCRATCH;
CREATE TABLE t (id INT PRIMARY KEY, x INT, CHECK (x > 0));
INSERT INTO t VALUES (1, 1);
SELECT * FROM t;
SQL
then
  echo "FAIL: root could not create and fill a database." >&2
  exit 1
fi
echo "OK: can create/drop databases and tables, insert, and select."

# CHECK constraints are silently ignored before MySQL 8.0.16.
if [[ "$VERSION" != *MariaDB* ]] && [[ "$(printf '%s\n8.0.16\n' "${VERSION%%-*}" | sort -V | head -1)" != "8.0.16" ]]; then
  echo "WARNING: MySQL $VERSION ignores CHECK constraints (needs 8.0.16+); the Step 1 'CHECK' demo will not fail." >&2
fi
echo "Ready: start with  mysql < 01_schema/schema.sql   (or ./run_demo.sh)"
