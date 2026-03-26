# Contributing

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) >= 24.0
- [Docker Compose](https://docs.docker.com/compose/install/) >= 2.0
- Python 3.12+ (for exporter development)

## Development Setup

```bash
git clone https://github.com/shivajichaprana/observability-stack.git
cd observability-stack

# Start the stack
./scripts/start.sh

# View dashboards
open http://localhost:3000
```

## Making Changes

**Prometheus configs:** Edit files in `docker-compose/prometheus/`, then reload:
```bash
curl -X POST http://localhost:9090/-/reload
```

**Grafana dashboards:** Edit JSON files in `docker-compose/grafana/dashboards/`. Grafana auto-reloads every 30 seconds.

**AlertManager config:** Edit `docker-compose/alertmanager/alertmanager.yml`, then restart:
```bash
docker compose restart alertmanager
```

**Demo exporter:** Edit `exporters/demo-exporter/exporter.py`, then rebuild:
```bash
docker compose up -d --build demo-exporter
```

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):
```
feat: add latency heatmap to SLO dashboard
fix: correct burn-rate threshold in alert rules
docs: update runbook with Loki troubleshooting
```

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
