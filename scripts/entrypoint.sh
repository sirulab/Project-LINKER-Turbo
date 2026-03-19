#!/bin/sh
# Container entrypoint — runs before the application starts.
#
# Workflow:
#   1. Wait for the database to be reachable (PostgreSQL only).
#   2. Apply any pending Alembic migrations.
#   3. Hand off to Uvicorn via exec (replaces shell process so signals work).
#
# SQLite (local dev without Docker): this script is NOT used;
# the server is started directly with `uvicorn src.main:app --reload`.

set -e

echo "========================================="
echo "  Project LINKER Turbo — Container Start"
echo "========================================="

# ── Run Alembic migrations ────────────────────────────────────────────────────
echo "--> Running database migrations (alembic upgrade head)..."
alembic upgrade head
echo "--> Migrations complete."

# ── Start the application ─────────────────────────────────────────────────────
echo "--> Starting Uvicorn on 0.0.0.0:8000 ..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 2
