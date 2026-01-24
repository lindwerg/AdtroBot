"""Custom Prometheus metrics for AdtroBot."""

from prometheus_client import Counter, Gauge, Histogram

# === Request Metrics ===
REQUESTS_TOTAL = Counter(
    "adtrobot_requests_total",
    "Total HTTP requests",
    labelnames=["handler", "method", "status"],
)

ERRORS_TOTAL = Counter(
    "adtrobot_errors_total",
    "Total errors by type",
    labelnames=["handler", "error_type"],
)

# === AI Operation Metrics ===
AI_REQUEST_DURATION = Histogram(
    "adtrobot_ai_request_duration_seconds",
    "AI request duration in seconds",
    labelnames=["operation", "model"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

AI_TOKENS_TOTAL = Counter(
    "adtrobot_ai_tokens_total",
    "Total AI tokens used",
    labelnames=["operation", "model", "token_type"],  # token_type: prompt/completion
)

AI_COST_TOTAL = Counter(
    "adtrobot_ai_cost_dollars_total",
    "Total AI cost in dollars",
    labelnames=["operation", "model"],
)

AI_REQUESTS_TOTAL = Counter(
    "adtrobot_ai_requests_total",
    "Total AI requests",
    labelnames=["operation", "model", "status"],  # status: success/error
)

# === Active Users Metrics ===
ACTIVE_USERS = Gauge(
    "adtrobot_active_users",
    "Active users count",
    labelnames=["period"],  # dau/wau/mau
)

# === Business Metrics ===
SUBSCRIPTION_CONVERSIONS = Counter(
    "adtrobot_subscription_conversions_total",
    "Total subscription conversions",
)

REVENUE_TOTAL = Counter(
    "adtrobot_revenue_rubles_total",
    "Total revenue in rubles",
)

# === Queue Metrics ===
QUEUE_DEPTH = Gauge(
    "adtrobot_queue_depth",
    "Background queue depth",
    labelnames=["status"],  # pending/failed/completed
)

# === Health Metrics ===
HEALTH_CHECK_STATUS = Gauge(
    "adtrobot_health_check_status",
    "Health check status (1=healthy, 0=unhealthy)",
    labelnames=["check"],  # database/scheduler/openrouter/telegram
)
