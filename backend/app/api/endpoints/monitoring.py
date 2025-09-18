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