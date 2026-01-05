#!/usr/bin/env bash
# reset_db.sh — drops and recreates the database, runs migrations, seeds demo data.
# WARNING: destroys all data. Dev use only.
set -euo pipefail

cd "$(dirname "$0")/../backend"

echo "⚠  This will destroy all data. Press Ctrl-C to cancel, or Enter to continue."
read -r

echo "→ Dropping and recreating database..."
alembic downgrade base
alembic upgrade head

echo "→ Seeding demo data..."
python ../scripts/seed.py

echo "✓ Reset complete."
