from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
import logging
import traceback
from datetime import datetime

from app.core.database import get_db
from app.core.config import settings
from app.models.models import PDFDocument, PDFPage
from app.models.user_models import User
from app.services.pdf_service import PDFService
from app.services.translation_service import TranslationService
from app.workers.celery_worker import process_document_translation
from app.api.endpoints.auth import get_current_user
import aiofiles

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload", response_model=dict)
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload PDF document with comprehensive error handling and logging"""
    
    # Log upload attempt
    safe_size = getattr(file, "size", None)
    logger.info(f"Upload attempt started: filename={file.filename}, content_type={file.content_type}, size={safe_size}")
    
    try:
        # Enhanced file validation
        if not file.filename:
            error_msg = "No filename provided"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        if not file.filename.lower().endswith('.pdf'):
            error_msg = f"Only PDF files are allowed. Received: {file.filename}"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Check file size
        if safe_size is not None and safe_size > settings.MAX_FILE_SIZE:
            error_msg = f"File too large. Maximum size: {settings.MAX_FILE_SIZE} bytes, received: {file.size} bytes"
            logger.error(error_msg)
            raise HTTPException(status_code=413, detail=error_msg)
        
        # Check if file is empty
        if safe_size == 0:
            error_msg = "File is empty"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Create upload directory if not exists
        try:
            os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
            logger.debug(f"Upload directory ensured: {settings.UPLOAD_DIR}")
        except Exception as e:
            error_msg = f"Failed to create upload directory: {str(e)}"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.pdf"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        logger.info(f"Generated file path: {file_path}")
        
        # Save file with error handling
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            
            # Verify file was written correctly
            if not os.path.exists(file_path):
                error_msg = "File was not saved successfully"
                logger.error(error_msg)
                raise HTTPException(status_code=500, detail=error_msg)
            
            actual_size = os.path.getsize(file_path)
            if actual_size != len(content):
                error_msg = f"File size mismatch. Expected: {len(content)}, Actual: {actual_size}"
                logger.error(error_msg)
                raise HTTPException(status_code=500, detail=error_msg)
            
            logger.info(f"File saved successfully: {file_path}, size: {actual_size} bytes")
            
        except Exception as e:
            error_msg = f"Failed to save file: {str(e)}"
            logger.error(error_msg, exc_info=True)
            # Clean up partial file
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.debug(f"Cleaned up partial file: {file_path}")
                except:
                    pass
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Save to database with error handling
        try:
            pdf_doc = PDFService.save_pdf_to_db(db, filename, file.filename, file_path)
            logger.info(f"Document saved to database: id={pdf_doc.id}, uuid={pdf_doc.uuid}")
        except Exception as e:
            error_msg = f"Failed to save document to database: {str(e)}"
            logger.error(error_msg, exc_info=True)
            # Clean up saved file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Cleaned up file after DB error: {file_path}")
            except:
                pass
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Extract pages with error handling
        try:
            total_pages = PDFService.extract_and_save_pages(db, pdf_doc.id, file_path)
            logger.info(f"Pages extracted successfully: {total_pages} pages")
        except Exception as e:
            error_msg = f"Failed to extract pages: {str(e)}"
            logger.warning(error_msg, exc_info=True)
            # Don't fail the upload if page extraction fails
            total_pages = 0
        
        logger.info(f"Upload completed successfully: document_id={pdf_doc.id}")
        
        return {
            "message": "File uploaded successfully",
            "document_id": pdf_doc.id,
            "uuid": pdf_doc.uuid,
            "total_pages": total_pages,
            "file_size_bytes": actual_size
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any unexpected errors
        error_msg = f"Unexpected error during upload: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during upload")

@router.get("/{document_id}", response_model=dict)
async def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get document details"""
    document = db.query(PDFDocument).filter(PDFDocument.id == document_id).first()
    if not document:
        raise HTTPException(404, "Document not found")
    
    return {
        "id": document.id,
        "uuid": document.uuid,
        "filename": document.original_filename,
        "status": document.status,
        "total_pages": document.total_pages,
        "total_characters": document.total_characters,
        "file_size_bytes": getattr(document, 'file_size_bytes', 0),
        "created_at": document.created_at
    }

@router.get("/{document_id}/pages", response_model=List[dict])
async def get_document_pages(document_id: int, db: Session = Depends(get_db)):
    """Get all pages for a document"""
    pages = db.query(PDFPage).filter(PDFPage.document_id == document_id).all()
    
    return [{
        "id": page.id,
        "page_number": page.page_number,
        "char_count": page.char_count,
        "translation_status": page.translation_status,
        "translated_text": page.translated_text,
        "tokens_in": getattr(page, 'tokens_in', 0),
        "tokens_out": getattr(page, 'tokens_out', 0),
        "cost_estimate": getattr(page, 'cost_estimate', 0.0),
        "is_test_page": page.is_test_page,
        "created_at": page.created_at
    } for page in pages]

@router.post("/{document_id}/translate")
async def start_translation(
    document_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start translation process for document"""
    document = db.query(PDFDocument).filter(PDFDocument.id == document_id).first()
    if not document:
        raise HTTPException(404, "Document not found")
    
    # Start celery task
    task = process_document_translation.delay(document_id)
    
    return {"message": "Translation started", "task_id": task.id}

@router.post("/{document_id}/pages/{page_number}/test")
async def mark_test_page(
    document_id: int, 
    page_number: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark page as test page and translate it"""
    try:
        page = PDFService.mark_page_as_test(db, document_id, page_number)
        if not page:
            raise HTTPException(404, "Page not found")
        
        # Translate the test page
        translation_service = TranslationService()
        translated_page = translation_service.translate_page(db, page.id)
        
        return {
            "message": "Test page translated",
            "page_number": page_number,
            "translated_text": translated_page.translated_text
        }
    except ValueError as e:
        # Handle translation service errors (quota, auth, etc.)
        error_message = str(e)
        if "quota exceeded" in error_message.lower():
            raise HTTPException(402, error_message)  # Payment Required
        elif "authentication failed" in error_message.lower():
            raise HTTPException(503, error_message)  # Service Unavailable
        elif "temporarily unavailable" in error_message.lower():
            raise HTTPException(503, error_message)  # Service Unavailable
        else:
            raise HTTPException(500, error_message)
    except Exception as e:
        logger.error(f"Unexpected error in test translation: {e}")
        raise HTTPException(500, f"Test translation failed: {str(e)}")
