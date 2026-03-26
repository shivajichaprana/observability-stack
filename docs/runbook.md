# Operations Runbook

## Quick Start

```bash
cd docker-compose
docker compose up -d

# Access points:
# Grafana:      http://localhost:3000 (admin / observability)
# Prometheus:   http://localhost:9090
# AlertManager: http://localhost:9093
# Loki:         http://localhost:3100
# Demo Exporter: http://localhost:8000/metrics
```

## Alert Response Procedures

### High CPU Usage
**Severity:** Warning (>80%), Critical (>95%)

1. Check which process is consuming CPU: `docker stats` or `top`
2. If container-specific, check container logs: `docker logs <container>`
3. Consider scaling horizontally if load-related
4. Check for runaway queries in Prometheus (heavy recording rules)

### High Memory Usage
**Severity:** Warning (>85%)

1. Check memory consumers: `docker stats --no-stream`
2. Prometheus TSDB can grow — check retention settings
3. Loki chunk storage may need tuning
4. Consider adjusting container memory limits

### Disk Space Running Low
**Severity:** Warning (<15%), Critical (<5%)

1. Check Prometheus data retention: default is 15 days
2. Clean old Loki chunks: check `table_manager.retention_period`
3. Prune Docker images: `docker system prune -f`
4. Check Grafana database size

### High Error Rate
**Severity:** Warning (>5%), Critical (>10%)

1. Check which endpoints are failing: Grafana → Application dashboard
2. Review error logs in Loki: `{container="demo-exporter"} |= "error"`
3. Check upstream dependencies
4. Review recent deployments

### SLO Burn Rate — Fast
**Severity:** Critical (14.4x burn rate)

This means 2% of the monthly error budget is being consumed per hour. At this rate, the budget will be exhausted in ~70 minutes.

1. Check the SLO Dashboard for affected services
2. Identify the error source (5xx status codes by endpoint)
3. Check recent changes or deployments
4. Consider rolling back if a deployment caused the spike
5. Communicate status to stakeholders

### SLO Burn Rate — Slow
**Severity:** Warning (6x burn rate)

Budget consumption is elevated but not critical. ~5 days until budget exhaustion.

1. Review error trends over the past 6 hours
2. Identify gradual degradation patterns
3. Create a ticket for investigation
4. Monitor for escalation to fast burn

## Maintenance

### Reloading Prometheus Config
```bash
curl -X POST http://localhost:9090/-/reload
```

### Checking AlertManager Status
```bash
curl -s http://localhost:9093/api/v2/status | python3 -m json.tool
```

### Viewing Active Alerts
```bash
curl -s http://localhost:9093/api/v2/alerts | python3 -m json.tool
```

### Querying Loki Logs
```bash
# Via Grafana Explore tab (recommended)
# Or via LogCLI:
# logcli query '{container="demo-exporter"}' --limit 100
```

### Backup and Restore

**Prometheus data:**
```bash
docker cp prometheus:/prometheus ./prometheus-backup
```

**Grafana dashboards:**
Already version-controlled in `grafana/dashboards/`.

## Scaling Considerations

For production Kubernetes deployments, consider the following for each component. Prometheus can be scaled with Thanos or Cortex for multi-cluster federation. Loki should be deployed in microservices mode for high-volume ingestion. Grafana supports horizontal scaling behind a load balancer with shared database.
