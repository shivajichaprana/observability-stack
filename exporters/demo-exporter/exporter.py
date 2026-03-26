"""
Demo Prometheus Exporter
Generates realistic-looking application metrics for dashboard demos.
Simulates an e-commerce API with variable load, latency, and error rates.
"""

import os
import time
import math
import random
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# ─── Metric Storage ────────────────────────────
metrics = {
    "http_requests_total": {},       # {method, endpoint, status} -> count
    "http_request_duration_seconds": {},  # histogram buckets
    "app_active_connections": 0,
    "app_items_in_cart": 0,
    "app_orders_processed_total": 0,
    "app_revenue_total": 0.0,
    "app_db_connections_active": 0,
    "app_cache_hits_total": 0,
    "app_cache_misses_total": 0,
}

# Histogram bucket boundaries (seconds)
LATENCY_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

# Endpoint definitions with baseline characteristics
ENDPOINTS = [
    {"method": "GET",  "path": "/api/products",     "base_latency": 0.05,  "error_rate": 0.001},
    {"method": "GET",  "path": "/api/products/{id}", "base_latency": 0.03,  "error_rate": 0.002},
    {"method": "POST", "path": "/api/cart",          "base_latency": 0.08,  "error_rate": 0.005},
    {"method": "POST", "path": "/api/orders",        "base_latency": 0.15,  "error_rate": 0.01},
    {"method": "GET",  "path": "/api/users/profile", "base_latency": 0.04,  "error_rate": 0.001},
    {"method": "POST", "path": "/api/auth/login",    "base_latency": 0.10,  "error_rate": 0.008},
    {"method": "GET",  "path": "/health",            "base_latency": 0.002, "error_rate": 0.0},
]

lock = threading.Lock()


def get_time_factor():
    """Simulate diurnal traffic patterns (higher during business hours)."""
    hour = time.localtime().tm_hour
    # Peak at 14:00, trough at 04:00
    return 0.3 + 0.7 * (math.sin((hour - 4) * math.pi / 12) + 1) / 2


def get_load_spike():
    """Occasionally simulate traffic spikes."""
    return random.random() < 0.05  # 5% chance of spike


def simulate_request(endpoint):
    """Simulate a single HTTP request with realistic characteristics."""
    method = endpoint["method"]
    path = endpoint["path"]
    base_latency = endpoint["base_latency"]
    error_rate = endpoint["error_rate"]

    # Determine status code
    spike = get_load_spike()
    adjusted_error_rate = error_rate * (3 if spike else 1)

    if random.random() < adjusted_error_rate:
        status = random.choice(["500", "502", "503"])
    elif random.random() < 0.01:
        status = "429"  # Rate limited
    elif random.random() < 0.005:
        status = "404"
    else:
        status = "200"

    # Calculate latency
    latency = base_latency * random.lognormvariate(0, 0.3)
    if spike:
        latency *= random.uniform(2, 5)
    if status.startswith("5"):
        latency *= random.uniform(1.5, 3)

    # Update counters
    key = f'{method}|{path}|{status}'
    with lock:
        metrics["http_requests_total"][key] = metrics["http_requests_total"].get(key, 0) + 1

        # Update histogram buckets
        for bucket in LATENCY_BUCKETS:
            bucket_key = f'{method}|{path}|{bucket}'
            if latency <= bucket:
                metrics["http_request_duration_seconds"][bucket_key] = (
                    metrics["http_request_duration_seconds"].get(bucket_key, 0) + 1
                )
        # +Inf bucket
        inf_key = f'{method}|{path}|+Inf'
        metrics["http_request_duration_seconds"][inf_key] = (
            metrics["http_request_duration_seconds"].get(inf_key, 0) + 1
        )

        # Sum for histogram
        sum_key = f'{method}|{path}|sum'
        metrics["http_request_duration_seconds"][sum_key] = (
            metrics["http_request_duration_seconds"].get(sum_key, 0) + latency
        )
        count_key = f'{method}|{path}|count'
        metrics["http_request_duration_seconds"][count_key] = (
            metrics["http_request_duration_seconds"].get(count_key, 0) + 1
        )

    return status, latency


def simulate_business_metrics():
    """Update business-level metrics."""
    with lock:
        metrics["app_active_connections"] = max(0, int(random.gauss(50, 15) * get_time_factor()))
        metrics["app_items_in_cart"] = max(0, int(random.gauss(120, 30) * get_time_factor()))
        metrics["app_db_connections_active"] = max(1, int(random.gauss(10, 3)))

        # Simulate cache behavior
        metrics["app_cache_hits_total"] += random.randint(5, 20)
        metrics["app_cache_misses_total"] += random.randint(0, 3)

        # Orders and revenue (during "business hours")
        if random.random() < 0.3 * get_time_factor():
            metrics["app_orders_processed_total"] += 1
            metrics["app_revenue_total"] += round(random.uniform(15.0, 250.0), 2)


def traffic_generator():
    """Background thread generating simulated traffic."""
    while True:
        time_factor = get_time_factor()
        num_requests = int(random.gauss(10, 3) * time_factor)
        num_requests = max(1, num_requests)

        for _ in range(num_requests):
            # Weight endpoints by realistic frequency
            weights = [30, 20, 15, 5, 15, 10, 5]
            endpoint = random.choices(ENDPOINTS, weights=weights, k=1)[0]
            simulate_request(endpoint)

        simulate_business_metrics()
        time.sleep(1)


def format_metrics():
    """Format all metrics in Prometheus exposition format."""
    lines = []

    # ─── HTTP Request Counter ──────────────
    lines.append("# HELP http_requests_total Total HTTP requests")
    lines.append("# TYPE http_requests_total counter")
    with lock:
        for key, count in sorted(metrics["http_requests_total"].items()):
            method, path, status = key.split("|")
            lines.append(
                f'http_requests_total{{method="{method}",endpoint="{path}",status="{status}"}} {count}'
            )

    # ─── HTTP Request Duration Histogram ───
    lines.append("")
    lines.append("# HELP http_request_duration_seconds HTTP request duration in seconds")
    lines.append("# TYPE http_request_duration_seconds histogram")
    with lock:
        # Group by method|path
        seen = set()
        for key in sorted(metrics["http_request_duration_seconds"].keys()):
            parts = key.split("|")
            method, path = parts[0], parts[1]
            mp = f"{method}|{path}"
            if mp in seen:
                continue
            seen.add(mp)

            for bucket in LATENCY_BUCKETS:
                bkey = f"{method}|{path}|{bucket}"
                val = metrics["http_request_duration_seconds"].get(bkey, 0)
                lines.append(
                    f'http_request_duration_seconds_bucket{{method="{method}",endpoint="{path}",le="{bucket}"}} {val}'
                )
            inf_key = f"{method}|{path}|+Inf"
            val = metrics["http_request_duration_seconds"].get(inf_key, 0)
            lines.append(
                f'http_request_duration_seconds_bucket{{method="{method}",endpoint="{path}",le="+Inf"}} {val}'
            )
            sum_val = metrics["http_request_duration_seconds"].get(f"{method}|{path}|sum", 0)
            count_val = metrics["http_request_duration_seconds"].get(f"{method}|{path}|count", 0)
            lines.append(
                f'http_request_duration_seconds_sum{{method="{method}",endpoint="{path}"}} {sum_val:.6f}'
            )
            lines.append(
                f'http_request_duration_seconds_count{{method="{method}",endpoint="{path}"}} {count_val}'
            )

    # ─── Application Gauges ────────────────
    lines.append("")
    lines.append("# HELP app_active_connections Number of active connections")
    lines.append("# TYPE app_active_connections gauge")
    lines.append(f'app_active_connections {metrics["app_active_connections"]}')

    lines.append("")
    lines.append("# HELP app_items_in_cart Number of items currently in carts")
    lines.append("# TYPE app_items_in_cart gauge")
    lines.append(f'app_items_in_cart {metrics["app_items_in_cart"]}')

    lines.append("")
    lines.append("# HELP app_db_connections_active Number of active database connections")
    lines.append("# TYPE app_db_connections_active gauge")
    lines.append(f'app_db_connections_active {metrics["app_db_connections_active"]}')

    # ─── Application Counters ──────────────
    lines.append("")
    lines.append("# HELP app_orders_processed_total Total orders processed")
    lines.append("# TYPE app_orders_processed_total counter")
    lines.append(f'app_orders_processed_total {metrics["app_orders_processed_total"]}')

    lines.append("")
    lines.append("# HELP app_revenue_total Total revenue in USD")
    lines.append("# TYPE app_revenue_total counter")
    lines.append(f'app_revenue_total {metrics["app_revenue_total"]:.2f}')

    lines.append("")
    lines.append("# HELP app_cache_hits_total Total cache hits")
    lines.append("# TYPE app_cache_hits_total counter")
    lines.append(f'app_cache_hits_total {metrics["app_cache_hits_total"]}')

    lines.append("")
    lines.append("# HELP app_cache_misses_total Total cache misses")
    lines.append("# TYPE app_cache_misses_total counter")
    lines.append(f'app_cache_misses_total {metrics["app_cache_misses_total"]}')

    return "\n".join(lines) + "\n"


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler serving Prometheus metrics."""

    def do_GET(self):
        if self.path == "/metrics":
            body = format_metrics()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.end_headers()
            self.wfile.write(body.encode())
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "healthy"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress request logging."""
        pass


def main():
    port = int(os.environ.get("EXPORTER_PORT", "8000"))

    # Start traffic simulation in background
    thread = threading.Thread(target=traffic_generator, daemon=True)
    thread.start()

    # Start metrics server
    server = HTTPServer(("0.0.0.0", port), MetricsHandler)
    print(f"Demo exporter started on port {port}")
    print(f"Metrics: http://localhost:{port}/metrics")
    print(f"Health:  http://localhost:{port}/health")
    server.serve_forever()


if __name__ == "__main__":
    main()
