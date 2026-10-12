#!/usr/bin/env bash
# One command to reset and start the whole demo:
#   ./run_demo.sh            # drop/create DB, seed, start the app on :5000
# Reads settings from .env if present (see .env.example).
set -euo pipefail
cd "$(dirname "$0")"

if [[ -f .env ]]; then set -a; source .env; set +a; fi

MYSQL=(mysql)
[[ -n "${DB_USER:-}"   ]] && MYSQL+=(-u "$DB_USER")
[[ -n "${DB_HOST:-}"   ]] && MYSQL+=(-h "$DB_HOST")
[[ -n "${DB_PORT:-}"   ]] && MYSQL+=(-P "$DB_PORT")
[[ -n "${DB_SOCKET:-}" ]] && MYSQL+=(--socket "$DB_SOCKET")
[[ -n "${DB_PASSWORD:-}" ]] && export MYSQL_PWD="$DB_PASSWORD"   # keeps it out of `ps`

echo "== Step 1: schema";  "${MYSQL[@]}" < 01_schema/schema.sql
echo "== Step 2: seed";    python 02_seed/seed.py
echo "== Steps 4-5: app on http://localhost:5000"
exec python 04_backend/app.py
