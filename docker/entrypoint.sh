#!/bin/bash
set -e

echo "Running migrations..."
alembic upgrade head

echo "Creating admin user..."
echo "Username: $ADMIN_USERNAME"
echo "Email: $ADMIN_EMAIL"
python -m qubit.scripts.create_admin create-admin --username "$ADMIN_USERNAME" --email "$ADMIN_EMAIL" --password "$ADMIN_PASSWORD" --config /app/data/config.yaml

echo "Starting application..."
python -m qubit.main --config /app/data/config.yaml 