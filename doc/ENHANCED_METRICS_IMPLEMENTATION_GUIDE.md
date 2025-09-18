# Enhanced Metrics Implementation Guide

## Overview

This guide provides step-by-step instructions to integrate comprehensive metrics into your existing translation system, building on your current Prometheus setup to create production-grade observability.

## Current State Assessment

Your current metrics foundation:
- ✅ Basic `translation_requests`, `translation_errors`, `translation_latency` in `app/metrics.py`
- ✅ `/metrics` endpoint exposed in FastAPI
- ✅ Metrics integrated in `Translator.translate_text()` method
- ✅ Prometheus client configured and working

## Implementation Steps

### Step 1: Enhance Metrics Collection (15 minutes)

**1.1 Update the existing metrics.py file**

Replace your current `backend/app/metrics.py` with enhanced version:

```python
# backend/app/metrics.py
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
```

### Step 2: Update Translator Service (10 minutes)

**2.1 Modify your Translator class**

Update `backend/app/services/translator.py` to use enhanced metrics:

```python
# backend/app/services/translator.py
from __future__ import annotations

from typing import Dict
from sqlalchemy.orm import Session

from app.models.models import PDFPage
from app.services.chunker import Chunker
from app.services.llm_client import LLMClient, OpenAIChatClient, estimate_cost_usd
from app.metrics import MetricsCollector  # Updated import
from app.services.prompt_library import PARAGRAPH_SYSTEM, paragraph_user


class Translator:
    def __init__(self, llm: LLMClient | None = None, chunk_tokens: int = 1200):
        self.llm = llm or OpenAIChatClient()
        self.chunker = Chunker(target_tokens=chunk_tokens)

    def translate_text(self, text: str) -> Dict:
        """Translate text using chunking and chat API; returns dict with text and usage."""
        if not text.strip():
            return {"text": "", "prompt_tokens": 0, "completion_tokens": 0, "cost_usd": 0.0}

        chunks = self.chunker.chunk_paragraphs(text)
        out_parts: list[str] = []
        ptoks = 0
        ctoks = 0

        for ch in chunks:
            # Start metrics collection
            start_time = MetricsCollector.record_translation_start(
                "translator.translate_text", "chat", "gpt-4o-mini"
            )

            try:
                res = self.llm.chat(PARAGRAPH_SYSTEM, paragraph_user(ch.text), temperature=0.1, max_tokens=800)

                # Record success
                MetricsCollector.record_translation_success(
                    start_time=start_time,
                    path="translator.translate_text",
                    mode="chat",
                    model="gpt-4o-mini",
                    tokens_in=res.prompt_tokens,
                    tokens_out=res.completion_tokens,
                    cost_usd=estimate_cost_usd(res.prompt_tokens, res.completion_tokens),
                    complexity=MetricsCollector.assess_text_complexity(ch.text)
                )

            except Exception as e:
                MetricsCollector.record_translation_error(
                    "translator.translate_text", "chat", type(e).__name__, str(e)
                )
                raise

            out_parts.append(res.text)
            ptoks += res.prompt_tokens
            ctoks += res.completion_tokens

        total_cost = estimate_cost_usd(ptoks, ctoks)
        return {
            "text": "\n\n".join(out_parts).strip(),
            "prompt_tokens": ptoks,
            "completion_tokens": ctoks,
            "cost_usd": total_cost,
        }

    def translate_page_chunked(self, db: Session, page_id: int) -> PDFPage:
        page = db.query(PDFPage).filter(PDFPage.id == page_id).first()
        if not page:
            raise ValueError("Page not found")

        # Start page-level metrics collection
        page_start_time = MetricsCollector.record_translation_start(
            "translator.translate_page_chunked", "chat", "gpt-4o-mini"
        )

        try:
            result = self.translate_text(page.original_text or "")
            page.translated_text = result["text"]
            page.translation_status = "completed"
            page.translation_model = "chat:gpt-4o-mini"
            page.cost_estimate = result["cost_usd"]

            # Store token usage
            try:
                page.tokens_in = int(result.get("prompt_tokens", 0))
                page.tokens_out = int(result.get("completion_tokens", 0))
            except Exception:
                pass

            db.commit()

            # Record page-level success metrics
            MetricsCollector.record_translation_success(
                start_time=page_start_time,
                path="translator.translate_page_chunked",
                mode="chat",
                model="gpt-4o-mini",
                tokens_in=page.tokens_in or 0,
                tokens_out=page.tokens_out or 0,
                cost_usd=page.cost_estimate or 0.0,
                complexity=MetricsCollector.assess_text_complexity(page.original_text or "")
            )

            return page

        except Exception as e:
            MetricsCollector.record_translation_error(
                "translator.translate_page_chunked", "chat", type(e).__name__, str(e)
            )
            raise
```

### Step 3: Add System Health Metrics (10 minutes)

**3.1 Create system monitoring endpoint**

Create `backend/app/api/endpoints/monitoring.py`:

```python
# backend/app/api/endpoints/monitoring.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.metrics import active_documents, celery_queue_length
from app.models.models import PDFDocument, TranslationJob

router = APIRouter()


@router.get("/system-health")
async def system_health(db: Session = Depends(get_db)):
    """Update system health metrics and return status"""

    # Count active documents (being processed)
    active_count = db.query(PDFDocument).join(TranslationJob).filter(
        TranslationJob.status.in_(["pending", "processing"])
    ).count()

    active_documents.set(active_count)

    # Get database connection count
    try:
        db_connections = db.execute(
            text("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
        ).scalar()
    except Exception:
        db_connections = 0

    # TODO: Add Redis monitoring if needed
    # TODO: Add Celery queue monitoring

    return {
        "status": "healthy",
        "active_documents": active_count,
        "database_connections": db_connections,
        "metrics_updated": True
    }
```

**3.2 Register the monitoring endpoint**

Update `backend/app/main.py` to include monitoring:

```python
# backend/app/main.py
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.api.endpoints import documents, enhanced_documents, monitoring  # Add monitoring
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://pdf.edcopo.info",
        "https://apipdf.edcopo.info"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(enhanced_documents.router, prefix="/api/enhanced", tags=["enhanced"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["monitoring"])  # Add this

@app.get("/")
async def root():
    return {"message": "PDF Translation Platform API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/metrics")
async def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
```

### Step 4: Setup Grafana Dashboard (15 minutes)

**4.1 Import the dashboard**

1. Copy the `monitoring/grafana-dashboard.json` to your Grafana instance
2. In Grafana UI: `+` → `Import` → paste JSON content
3. Configure data source to point to your Prometheus endpoint (`http://api:8000/metrics`)

**4.2 Configure Prometheus scraping**

Add to your `docker-compose.yml` or Prometheus config:

```yaml
# prometheus.yml (if you have Prometheus running)
scrape_configs:
  - job_name: 'pdf-translation'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Step 5: Test the Implementation (10 minutes)

**5.1 Restart your services**

```bash
docker-compose restart api worker
```

**5.2 Trigger some translations**

```bash
# Upload a test document and translate a page
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@test.pdf"

# Get document ID from response, then:
curl -X POST "http://localhost:8000/api/documents/{doc_id}/pages/1/test"
```

**5.3 Check metrics endpoint**

```bash
curl http://localhost:8000/metrics | grep translation_
```

You should see metrics like:
```
translation_requests_total{mode="chat",path="translator.translate_text"} 1.0
translation_tokens_input_total{model="gpt-4o-mini"} 150.0
translation_tokens_output_total{model="gpt-4o-mini"} 200.0
translation_cost_usd_total{document_type="pdf",model="gpt-4o-mini"} 0.001
```

**5.4 Check system health**

```bash
curl http://localhost:8000/api/monitoring/system-health
```

### Step 6: Validate Grafana Dashboard (5 minutes)

1. Open Grafana dashboard
2. Check that panels are showing data
3. Adjust time range if needed (try "Last 5 minutes")
4. Verify alerts are configured properly

## Troubleshooting

### Common Issues

**Issue**: Metrics not appearing in Grafana
**Solution**:
- Check Prometheus is scraping: `http://prometheus:9090/targets`
- Verify data source configuration in Grafana
- Check API metrics endpoint: `curl http://api:8000/metrics`

**Issue**: Some metrics show 0 values
**Solution**:
- Generate some activity (upload and translate documents)
- Check that MetricsCollector methods are being called
- Verify no exceptions in the translation pipeline

**Issue**: Dashboard panels show "No data"
**Solution**:
- Adjust time range in Grafana
- Check metric names match between code and dashboard
- Verify Prometheus is successfully scraping

## Next Steps

### Immediate (Today)
1. **Test the implementation** with sample translations
2. **Validate dashboard** shows real-time data
3. **Configure alerts** for cost thresholds

### Short-term (This Week)
1. **Add business metrics** (documents per day, user satisfaction)
2. **Configure alerting** (Slack/email notifications)
3. **Optimize dashboard** based on usage patterns

### Medium-term (Next Week)
1. **Add custom metrics** for specific business needs
2. **Create additional dashboards** (business intelligence, cost analysis)
3. **Implement automated reports** (daily/weekly summaries)

## Success Criteria

After implementation, you should have:
- ✅ Real-time cost monitoring with per-page granularity
- ✅ Performance metrics (latency, throughput, error rates)
- ✅ Business intelligence (document completion, queue health)
- ✅ Alerting on cost spikes and performance degradation
- ✅ Historical data for trend analysis and capacity planning

This enhanced metrics system will provide production-grade observability for your translation platform!