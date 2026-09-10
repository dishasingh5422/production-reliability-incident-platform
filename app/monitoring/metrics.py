from prometheus_client import Counter, Gauge, Histogram

REQUEST_COUNT = Counter(
    "reliability_http_requests_total",
    "HTTP request count",
    ("method", "path", "status"),
)
REQUEST_LATENCY = Histogram(
    "reliability_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ("method", "path"),
)
ERROR_COUNT = Counter(
    "reliability_http_errors_total",
    "HTTP 5xx response count",
    ("path",),
)
READINESS_STATE = Gauge(
    "reliability_readiness_state",
    "Current readiness state: 1 ready, 0 not ready",
)
DATABASE_CHECK_DURATION = Gauge(
    "reliability_database_check_duration_milliseconds",
    "Duration of the latest database readiness check",
)
BUILD_INFO = Gauge(
    "reliability_build_info",
    "Application build information",
    ("version", "environment"),
)
