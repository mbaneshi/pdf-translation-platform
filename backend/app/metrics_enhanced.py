from prometheus_client import Counter, Histogram, Gauge
import time

# Existing metrics from metrics.py
translation_requests = Counter(
    "translation_requests_total", "Number of translation requests", ["path", "mode"]
)

translation_errors = Counter(
    "translation_errors_total", "Translation errors", ["path", "mode", "reason"]
)

translation_latency = Histogram(
    "translation_latency_seconds", "Translation latency (seconds)", ["path", "mode"]
)

# Enhanced metrics for Grafana dashboard
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

average_pages_per_document = Histogram(
    "pages_per_document",
    "Distribution of pages per document",
    buckets=[1, 5, 10, 25, 50, 100, 200, 500]
)

# System health metrics
celery_queue_length = Gauge(
    "celery_queue_length", "Number of tasks in Celery queue", ["queue_name"]
)

database_connections = Gauge(
    "database_connections_active", "Number of active database connections"
)

redis_memory_usage = Gauge(
    "redis_memory_usage_bytes", "Redis memory usage in bytes"
)


class MetricsCollector:
    """Helper class to collect and record metrics consistently"""

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

        # Record latency
        translation_latency.labels(path=path, mode=mode).observe(duration)

        # Record page duration
        translation_page_duration.labels(complexity=complexity, model=model).observe(duration)

        # Record token usage
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
    def update_business_metrics(active_docs: int, completed_today: int):
        """Update business-level metrics"""
        active_documents.set(active_docs)
        documents_completed_today.inc(completed_today)

    @staticmethod
    def update_system_health(
        queue_length: int,
        db_connections: int,
        redis_memory: int
    ):
        """Update system health metrics"""
        celery_queue_length.labels(queue_name="default").set(queue_length)
        database_connections.set(db_connections)
        redis_memory_usage.set(redis_memory)


# Usage example for your Translator class:
"""
from app.metrics_enhanced import MetricsCollector

class Translator:
    def translate_page_chunked(self, db: Session, page_id: int) -> PDFPage:
        page = db.query(PDFPage).filter(PDFPage.id == page_id).first()
        if not page:
            raise ValueError("Page not found")

        # Start metrics collection
        start_time = MetricsCollector.record_translation_start(
            "translator.translate_page_chunked", "chat", "gpt-4o-mini"
        )

        try:
            result = self.translate_text(page.original_text or "")
            page.translated_text = result["text"]
            page.translation_status = "completed"
            page.translation_model = "chat:"
            page.cost_estimate = result["cost_usd"]
            page.tokens_in = int(result.get("prompt_tokens", 0))
            page.tokens_out = int(result.get("completion_tokens", 0))
            db.commit()

            # Record success metrics
            MetricsCollector.record_translation_success(
                start_time=start_time,
                path="translator.translate_page_chunked",
                mode="chat",
                model="gpt-4o-mini",
                tokens_in=page.tokens_in,
                tokens_out=page.tokens_out,
                cost_usd=page.cost_estimate,
                complexity=self._assess_complexity(page.original_text)
            )

            return page

        except Exception as e:
            MetricsCollector.record_translation_error(
                "translator.translate_page_chunked", "chat", type(e).__name__, str(e)
            )
            raise
"""