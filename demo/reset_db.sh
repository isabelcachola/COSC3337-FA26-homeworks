#!/usr/bin/env bash
# Reset the demo database from scratch.
#   ./reset_db.sh             drop the demo database (and all its tables), after asking
#   ./reset_db.sh -y          same, without asking
#   ./reset_db.sh --rebuild   drop it, then re-run steps 1-2 (schema, seed)
# Only the database named by DB_NAME (default club_events) is touched.
set -euo pipefail
cd "$(dirname "$0")"

ASSUME_YES=0
REBUILD=0
for arg in "$@"; do
  case "$arg" in
    -y|--yes)  ASSUME_YES=1 ;;
    --rebuild) REBUILD=1 ;;
    -h|--help) sed -n '2,6p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $arg (try --help)" >&2; exit 1 ;;
  esac
done

if [[ -f .env ]]; then set -a; source .env; set +a; fi
DB_NAME="${DB_NAME:-club_events}"

# DB_NAME ends up inside a SQL identifier, so allow only plain names.
if [[ ! "$DB_NAME" =~ ^[A-Za-z0-9_]+$ ]]; then
  echo "Refusing: DB_NAME '$DB_NAME' must contain only letters, digits and underscores." >&2
  exit 1
fi

MYSQL=(mysql)
[[ -n "${DB_USER:-}"   ]] && MYSQL+=(-u "$DB_USER")
[[ -n "${DB_HOST:-}"   ]] && MYSQL+=(-h "$DB_HOST")
[[ -n "${DB_PORT:-}"   ]] && MYSQL+=(-P "$DB_PORT")
[[ -n "${DB_SOCKET:-}" ]] && MYSQL+=(--socket "$DB_SOCKET")
[[ -n "${DB_PASSWORD:-}" ]] && export MYSQL_PWD="$DB_PASSWORD"   # keeps it out of `ps`

if [[ "$ASSUME_YES" -ne 1 ]]; then
  read -r -p "This permanently deletes database '$DB_NAME' and all its tables. Continue? [y/N] " answer
  [[ "$answer" =~ ^[Yy]$ ]] || { echo "Cancelled."; exit 0; }
fi

"${MYSQL[@]}" -e "DROP DATABASE IF EXISTS \`$DB_NAME\`"
echo "Dropped database '$DB_NAME'."

if [[ "$REBUILD" -eq 1 ]]; then
  [[ -x .venv/bin/python ]] || { echo "No .venv found; see README.md Setup." >&2; exit 1; }
  echo "== Step 1: schema";  "${MYSQL[@]}" < 01_schema/schema.sql
  echo "== Step 2: seed";    .venv/bin/python 02_seed/seed.py
  echo "Rebuilt '$DB_NAME'."
else
  echo "Rebuild with:  ./reset_db.sh --rebuild   (or run steps 1-2 by hand)"
fi
