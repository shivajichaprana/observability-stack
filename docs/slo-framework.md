# SLO Framework

## Overview

This observability stack implements Google's SRE approach to Service Level Objectives (SLOs) with multi-window burn-rate alerting. The framework tracks three key SLIs and alerts when error budgets are being consumed too quickly.

## Key Concepts

**SLI (Service Level Indicator):** A quantitative measure of service behavior. We track availability (success rate), latency (response time percentiles), and throughput (request rate).

**SLO (Service Level Objective):** A target value for an SLI. For example, "99.9% of requests succeed" or "P99 latency < 1 second."

**Error Budget:** The inverse of the SLO — the acceptable amount of failure. A 99.9% SLO gives a 0.1% error budget, meaning roughly 43 minutes of downtime per month.

## SLOs Defined

| SLI | SLO Target | Error Budget (30d) | Measurement Window |
|-----|-----------|-------------------|-------------------|
| Availability | 99.9% | 0.1% (~43 min) | Rolling 30 days |
| Latency (P99) | < 1 second | N/A | Rolling 5 minutes |
| Latency (P50) | < 500ms | N/A | Rolling 5 minutes |

## Burn-Rate Alerting

Traditional threshold alerts (e.g., "alert if error rate > 1%") have two problems: they fire too late for fast incidents and too early for slow degradation. Burn-rate alerting solves this by measuring how quickly the error budget is being consumed.

### How It Works

The **burn rate** is the ratio of actual error rate to the SLO's allowed error rate. A burn rate of 1x means you're consuming budget at exactly the sustainable rate. Higher means you'll run out sooner.

### Alert Windows

| Alert | Burn Rate | Long Window | Short Window | Budget Consumed | Action |
|-------|-----------|-------------|--------------|-----------------|--------|
| Fast burn | 14.4x | 1 hour | 5 minutes | 2% in 1h | Page on-call |
| Slow burn | 6x | 6 hours | 30 minutes | 5% in 6h | Create ticket |

The **two-window approach** prevents false positives. Both the long window (to confirm the trend) and short window (to confirm it's still happening) must exceed the threshold before the alert fires.

### Why These Thresholds

A 14.4x burn rate over 1 hour consumes 2% of the monthly budget. If sustained, the entire budget would be gone in roughly 70 minutes — that's a fast incident requiring immediate attention.

A 6x burn rate over 6 hours consumes 5% of the budget. If sustained, the budget would last about 5 days — slower degradation that needs investigation but not a 2 AM page.

## PromQL Queries

### Availability SLI
```promql
1 - (
  sum(rate(http_requests_total{status=~"5.."}[30d]))
  /
  sum(rate(http_requests_total[30d]))
)
```

### Error Budget Remaining
```promql
# Percentage of budget remaining
clamp_min(
  (1 - (
    sum(rate(http_requests_total{status=~"5.."}[30d]))
    / sum(rate(http_requests_total[30d]))
  ) / 0.001) * 100,
  0
)
```

### Burn Rate
```promql
# 1-hour burn rate
(sum(rate(http_requests_total{status=~"5.."}[1h])) / sum(rate(http_requests_total[1h]))) / 0.001
```

## Dashboard Layout

The SLO Dashboard provides three gauges at the top (availability, budget remaining, P99 latency), followed by time-series panels showing error rate trends, latency distribution, request rates by status code, and the multi-window burn rate visualization.

## References

- Google SRE Book: Chapter 4 — Service Level Objectives
- Google SRE Workbook: Chapter 5 — Alerting on SLOs
- Prometheus documentation on recording rules
