from prometheus_client import Counter, Histogram, Gauge
import time

# Existing metrics (keep these for compatibility)
translation_requests = Counter(
    "translation_requests_total", "Number of translation requests", ["path", "mode"]
)

translation_errors = Counter(
    "translation_errors_total", "Translation errors", ["path", "mode", "reason"]
)

translation_latency = Histogram(
    "translation_latency_seconds", "Translation latency (seconds)", ["path", "mode"]
)

# Enhanced metrics for comprehensive monitoring
translation_cost_usd = Counter(
    "translation_cost_usd_total", "Total translation costs in USD", ["model", "document_type"]
)

translation_tokens_input = Counter(
    "translation_tokens_input_total", "Total input tokens consumed", ["model"]
)

translation_tokens_output = Counter(
    "translation_tokens_output_total", "Total output tokens generated", ["model"]
)

translation_page_duration = Histogram(
    "translation_page_duration_seconds",
    "Time to translate a single page",
    ["complexity", "model"],
    buckets=[1, 5, 10, 30, 60, 120, 300]
)

translation_cost_per_page = Histogram(
    "translation_cost_per_page_usd",
    "Cost per page translation in USD",
    ["model", "complexity"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

# Business metrics
active_documents = Gauge(
    "active_documents_total", "Number of documents currently being processed"
)

documents_completed_today = Counter(
    "documents_completed_today_total", "Documents completed today"
)

# System health metrics
celery_queue_length = Gauge(
    "celery_queue_length", "Number of tasks in Celery queue", ["queue_name"]
)


class MetricsCollector:
    """Helper class for consistent metrics collection"""

    @staticmethod
    def record_translation_start(path: str, mode: str, model: str):
        """Record when a translation starts"""
        translation_requests.labels(path=path, mode=mode).inc()
        return time.time()

    @staticmethod
    def record_translation_success(
        start_time: float,
        path: str,
        mode: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
        cost_usd: float,
        complexity: str = "medium"
    ):
        """Record successful translation completion"""
        duration = time.time() - start_time

        # Record timing
        translation_latency.labels(path=path, mode=mode).observe(duration)
        translation_page_duration.labels(complexity=complexity, model=model).observe(duration)

        # Record usage
        translation_tokens_input.labels(model=model).inc(tokens_in)
        translation_tokens_output.labels(model=model).inc(tokens_out)

        # Record costs
        translation_cost_usd.labels(model=model, document_type="pdf").inc(cost_usd)
        translation_cost_per_page.labels(model=model, complexity=complexity).observe(cost_usd)

    @staticmethod
    def record_translation_error(path: str, mode: str, error_type: str, reason: str):
        """Record translation error"""
        translation_errors.labels(path=path, mode=mode, reason=reason).inc()

    @staticmethod
    def assess_text_complexity(text: str) -> str:
        """Simple complexity assessment for metrics"""
        if not text:
            return "empty"

        char_count = len(text)
        if char_count < 500:
            return "simple"
        elif char_count < 2000:
            return "medium"
        else:
            return "complex"

