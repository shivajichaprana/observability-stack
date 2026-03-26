#!/bin/bash
# start.sh - Start the full observability stack
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="${SCRIPT_DIR}/../docker-compose"

echo "═══════════════════════════════════════════"
echo " Starting Observability Stack"
echo "═══════════════════════════════════════════"
echo ""

cd "$COMPOSE_DIR"

echo "→ Building demo exporter..."
docker compose build demo-exporter

echo "→ Starting all services..."
docker compose up -d

echo ""
echo "→ Waiting for services to be healthy..."
sleep 5

# Check service health
services=("prometheus:9090" "grafana:3000" "alertmanager:9093" "loki:3100")
for svc in "${services[@]}"; do
    name="${svc%%:*}"
    port="${svc##*:}"
    if curl -sf "http://localhost:${port}/-/ready" > /dev/null 2>&1 || \
       curl -sf "http://localhost:${port}/api/health" > /dev/null 2>&1 || \
       curl -sf "http://localhost:${port}/ready" > /dev/null 2>&1; then
        echo "  ✓ ${name} is ready"
    else
        echo "  ⏳ ${name} is starting (port ${port})"
    fi
done

echo ""
echo "═══════════════════════════════════════════"
echo " Stack is running!"
echo ""
echo " Grafana:      http://localhost:3000"
echo "               Login: admin / observability"
echo " Prometheus:   http://localhost:9090"
echo " AlertManager: http://localhost:9093"
echo " Loki:         http://localhost:3100"
echo " Demo Metrics: http://localhost:8000/metrics"
echo "═══════════════════════════════════════════"
