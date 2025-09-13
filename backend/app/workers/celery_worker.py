from celery import Celery
from app.core.config import settings
from app.core.database import SessionLocal
from app.services.translation_service import TranslationService
from app.models.models import PDFPage, TranslationJob
import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

celery_app = Celery(
    'translation_worker',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

@celery_app.task(bind=True, max_retries=3)
def translate_page_task(self, page_id: int, job_id: int):
    """Celery task to translate a single page"""
    db = SessionLocal()
    translation_service = TranslationService()
    
    try:
        # Update job progress
        job = db.query(TranslationJob).filter(TranslationJob.id == job_id).first()
        if job:
            job.pages_processed += 1
            db.commit()
        
        # Translate the page
        page = translation_service.translate_page(db, page_id)
        logger.info(f"Translated page {page.page_number}")
        
        return {"status": "success", "page_id": page_id}
        
    except Exception as e:
        logger.error(f"Error translating page {page_id}: {e}")
        self.retry(exc=e, countdown=60)
        
    finally:
        db.close()

@celery_app.task(bind=True)
def process_document_translation(self, document_id: int):
    """Process entire document translation"""
    db = SessionLocal()
    
    try:
        # Create translation job
        job = TranslationJob(
            document_id=document_id,
            celery_task_id=self.request.id,
            status="processing",
            total_pages=db.query(PDFPage).filter(PDFPage.document_id == document_id).count(),
            started_at=db.func.now()
        )
        db.add(job)
        db.commit()
        
        # Get pages to translate
        pages = db.query(PDFPage).filter(
            PDFPage.document_id == document_id,
            PDFPage.translation_status == "pending"
        ).all()
        
        # Start translation tasks
        for page in pages:
            translate_page_task.delay(page.id, job.id)
        
        job.status = "started"
        db.commit()
        
        return {"status": "started", "job_id": job.id, "total_pages": len(pages)}
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        if job:
            job.status = "failed"
            db.commit()
        raise e
        
    finally:
        db.close()
