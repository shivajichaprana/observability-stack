#!/bin/bash
# stop.sh - Stop and clean up the observability stack
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="${SCRIPT_DIR}/../docker-compose"

cd "$COMPOSE_DIR"

echo "Stopping observability stack..."
docker compose down

echo ""
echo "Stack stopped. Data volumes are preserved."
echo "To remove all data: docker compose down -v"
