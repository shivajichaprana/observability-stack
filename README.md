# observability-stack

![License](https://img.shields.io/badge/license-MIT-green.svg)
![Prometheus](https://img.shields.io/badge/Prometheus-2.51-E6522C.svg)
![Grafana](https://img.shields.io/badge/Grafana-10.4-F46800.svg)
![Docker Compose](https://img.shields.io/badge/Docker_Compose-ready-2496ED.svg)

Production-ready observability platform with Prometheus metrics, Grafana dashboards, AlertManager alerting, and Loki log aggregation. Includes SLO tracking with multi-window burn-rate alerts, pre-built dashboards, and a demo exporter that generates realistic application metrics. One command to deploy.

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    Observability Stack                            │
│                                                                  │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────────┐    │
│  │ Demo App    │    │ Node         │    │ cAdvisor         │    │
│  │ Exporter    │    │ Exporter     │    │ (containers)     │    │
│  │ :8000       │    │ :9100        │    │ :8080            │    │
│  └──────┬──────┘    └──────┬───────┘    └────────┬─────────┘    │
│         │                  │                     │              │
│         └──────────────────┼─────────────────────┘              │
│                            │ scrape                             │
│                            ▼                                    │
│  ┌─────────────────────────────────────────┐                    │
│  │            Prometheus :9090             │                    │
│  │                                         │                    │
│  │  • Recording rules (pre-computed SLIs)  │                    │
│  │  • Alert rules (infra + app + SLO)      │                    │
│  │  • 15-day retention                     │                    │
│  └────────┬──────────────────┬─────────────┘                    │
│           │                  │                                  │
│           │ query            │ alerts                           │
│           ▼                  ▼                                  │
│  ┌─────────────────┐  ┌──────────────────┐                     │
│  │  Grafana :3000  │  │ AlertManager     │                     │
│  │                 │  │ :9093            │                     │
│  │  • SLO Dashboard│  │                  │                     │
│  │  • Infra Dash   │  │ • Slack routes   │                     │
│  │  • App Metrics  │  │ • PagerDuty      │                     │
│  └────────┬────────┘  │ • Severity-based │                     │
│           │           └──────────────────┘                     │
│           │ query                                               │
│           ▼                                                     │
│  ┌─────────────────────────────────────────┐                    │
│  │              Loki :3100                 │                    │
│  │                                         │                    │
│  │  ◄──── Promtail (log shipper)          │                    │
│  │        • Docker container logs          │                    │
│  │        • System logs                    │                    │
│  └─────────────────────────────────────────┘                    │
└──────────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
git clone https://github.com/shivajichaprana/observability-stack.git
cd observability-stack

# Start everything
./scripts/start.sh

# Or manually:
cd docker-compose && docker compose up -d
```

Then open **http://localhost:3000** (login: `admin` / `observability`). The SLO Dashboard loads as the home page with live metrics from the demo exporter.

## What's Included

**3 Pre-built Grafana Dashboards** — SLO Dashboard (availability gauge, error budget, burn-rate visualization), Infrastructure Overview (CPU, memory, disk, network, container metrics), Application Metrics (request rates, latency percentiles, cache hit ratios, business metrics).

**Prometheus Recording Rules** — Pre-computed SLI metrics for efficient dashboard queries. HTTP request rates, error rates, and latency percentiles (P50/P90/P99) by job. Multi-window error ratios for burn-rate alerting (5m, 30m, 1h, 6h windows).

**Alert Rules (3 categories)** — Infrastructure alerts for CPU, memory, disk with warning/critical thresholds. Application alerts for error rate and latency spikes. SLO burn-rate alerts using Google's multi-window approach (fast burn: page immediately, slow burn: create ticket).

**AlertManager Routing** — Severity-based routing to Slack channels (#alerts-warning, #alerts-critical, #slo-alerts). PagerDuty integration for critical alerts. Inhibition rules to suppress warnings when criticals fire. Configurable group intervals and repeat timers.

**Loki Log Aggregation** — Docker container log collection via Promtail with automatic label extraction. Log level parsing (INFO, WARN, ERROR). System log collection. 7-day retention with configurable limits.

**Demo Exporter** — Python-based Prometheus exporter simulating an e-commerce API. Generates realistic HTTP metrics with diurnal patterns, occasional traffic spikes, and variable error rates. Business metrics including orders, revenue, cache behavior, and database connections.

## Dashboards

### SLO Dashboard
Tracks availability SLO (99.9% target), error budget consumption, P99 latency, error rate trends, request distribution by status code, and multi-window burn rate visualization.

### Infrastructure Overview
Host-level metrics from Node Exporter (CPU, memory, disk, network I/O) and container-level metrics from cAdvisor (per-container CPU and memory).

### Application Metrics
Request rate and error rate stats, per-endpoint latency (P99), cache hit ratio, active connections, database connection pool, and cumulative revenue tracking.

## SLO Framework

The stack implements SLO burn-rate alerting based on Google's SRE practices:

| Alert | Burn Rate | Time Window | Budget Impact | Action |
|-------|-----------|-------------|---------------|--------|
| Fast burn | 14.4x | 1h + 5m | 2% / hour | Page on-call |
| Slow burn | 6x | 6h + 30m | 5% / 6 hours | Create ticket |

See [docs/slo-framework.md](./docs/slo-framework.md) for the full explanation of burn-rate calculations and PromQL queries.

## Project Structure

```
observability-stack/
├── docker-compose/
│   ├── docker-compose.yml          # Full stack definition (7 services)
│   ├── prometheus/
│   │   ├── prometheus.yml          # Scrape configs for all targets
│   │   ├── alert-rules.yml         # 12 alert rules (infra + app + SLO)
│   │   └── recording-rules.yml     # Pre-computed SLI metrics
│   ├── grafana/
│   │   ├── datasources.yml         # Auto-provisioned (Prometheus, Loki, AlertManager)
│   │   ├── dashboard-providers.yml # Dashboard auto-loading
│   │   └── dashboards/
│   │       ├── slo-dashboard.json      # SLO tracking with burn-rate
│   │       ├── infrastructure.json     # Host + container metrics
│   │       └── application.json        # App metrics + business KPIs
│   ├── alertmanager/
│   │   └── alertmanager.yml        # Routing: Slack + PagerDuty
│   ├── loki/
│   │   └── loki-config.yml         # Log storage and retention
│   └── promtail/
│       └── promtail-config.yml     # Docker + system log collection
├── exporters/
│   └── demo-exporter/
│       ├── exporter.py             # Python metrics generator (~250 LOC)
│       ├── Dockerfile
│       └── requirements.txt
├── scripts/
│   ├── start.sh                    # One-command stack startup
│   └── stop.sh                     # Clean shutdown
├── docs/
│   ├── slo-framework.md            # SLO/SLI definitions and burn-rate math
│   └── runbook.md                  # Alert response procedures
├── CONTRIBUTING.md
└── README.md
```

## Configuration

### Environment-Specific Settings

| Setting | Default | Description |
|---------|---------|-------------|
| Grafana admin password | `observability` | Change via `GF_SECURITY_ADMIN_PASSWORD` |
| Prometheus retention | 15 days | Adjust `--storage.tsdb.retention.time` |
| Loki retention | 7 days | Adjust `table_manager.retention_period` |
| Scrape interval | 15 seconds | Set in `prometheus.yml` global config |
| Demo exporter port | 8000 | Change via `EXPORTER_PORT` env var |

### Integrating Real Services

Replace or extend the Prometheus scrape configs to point at your actual services. The recording rules and alert rules work with any service exposing standard HTTP metrics (`http_requests_total`, `http_request_duration_seconds`).

## Operations

```bash
# Start stack
./scripts/start.sh

# Stop stack (preserves data)
./scripts/stop.sh

# Stop and remove all data
cd docker-compose && docker compose down -v

# Reload Prometheus config without restart
curl -X POST http://localhost:9090/-/reload

# Check active alerts
curl -s http://localhost:9093/api/v2/alerts | python3 -m json.tool
```

See [docs/runbook.md](./docs/runbook.md) for detailed alert response procedures.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for development setup and guidelines.

## License

MIT — see [LICENSE](./LICENSE) for details.
