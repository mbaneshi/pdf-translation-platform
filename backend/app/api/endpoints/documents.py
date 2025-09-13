from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import os
import uuid
from datetime import datetime

from app.core.database import get_db
from app.core.config import settings
from app.models.enhanced_models import PDFDocument, PDFPage
from app.services.pdf_service import PDFService
from app.services.translation_service import TranslationService
from app.workers.celery_worker import process_document_translation
import aiofiles

router = APIRouter()

@router.post("/upload", response_model=dict)
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload PDF document"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are allowed")
    
    # Create upload directory if not exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    filename = f"{file_id}.pdf"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Save to database
    pdf_doc = PDFService.save_pdf_to_db(db, filename, file.filename, file_path)
    
    # Extract pages in background
    PDFService.extract_and_save_pages(db, pdf_doc.id, file_path)
    
    return {
        "message": "File uploaded successfully",
        "document_id": pdf_doc.id,
        "uuid": pdf_doc.uuid
    }

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
        "is_test_page": page.is_test_page,
        "created_at": page.created_at
    } for page in pages]

@router.post("/{document_id}/translate")
async def start_translation(document_id: int, db: Session = Depends(get_db)):
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
    db: Session = Depends(get_db)
):
    """Mark page as test page and translate it"""
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
