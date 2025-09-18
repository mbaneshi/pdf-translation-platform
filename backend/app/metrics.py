from prometheus_client import Counter, Histogram

translation_requests = Counter(
    "translation_requests_total", "Number of translation requests", ["path", "mode"]
)

translation_errors = Counter(
    "translation_errors_total", "Translation errors", ["path", "mode", "reason"]
)

translation_latency = Histogram(
    "translation_latency_seconds", "Translation latency (seconds)", ["path", "mode"]
)

