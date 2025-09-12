# Enhanced API Endpoints for Semantic PDF Translation
# backend/app/api/endpoints/enhanced_documents.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import os
import uuid
from datetime import datetime

from core.database import get_db
from core.config import settings
from models.enhanced_models import PDFDocument, PDFPage, SemanticStructure, SampleTranslation, TranslationJob
from services.pdf_service import PDFService
from services.enhanced_pdf_service import EnhancedPDFService
from services.semantic_analyzer import SemanticAnalyzer
from services.translation_service import TranslationService
from workers.celery_worker import process_document_translation
import aiofiles

router = APIRouter()

@router.post("/upload-enhanced", response_model=dict)
async def upload_pdf_enhanced(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload PDF document with enhanced processing and layout preservation"""
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
    
    # Get file size
    file_size = os.path.getsize(file_path)
    
    try:
        # Use enhanced PDF service for layout preservation
        enhanced_service = EnhancedPDFService()
        pdf_doc = enhanced_service.save_enhanced_pdf_to_db(db, filename, file.filename, file_path)
        
        return {
            "message": "File uploaded successfully with enhanced processing",
            "document_id": pdf_doc.id,
            "uuid": pdf_doc.uuid,
            "total_pages": pdf_doc.total_pages,
            "file_size_bytes": file_size,
            "layout_preservation": True,
            "enhanced_features": ["layout_analysis", "table_detection", "format_preservation"]
        }
        
    except Exception as e:
        # Fallback to basic processing
        logger.warning(f"Enhanced processing failed, falling back to basic: {e}")
        
        pdf_doc = PDFDocument(
            filename=filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size_bytes=file_size,
            status="uploaded"
        )
        
        db.add(pdf_doc)
        db.commit()
        db.refresh(pdf_doc)
        
        # Extract pages and basic info
        total_pages = PDFService.extract_and_save_pages(db, pdf_doc.id, file_path)
        
        # Update document with page count
        pdf_doc.total_pages = total_pages
        db.commit()
        
        return {
            "message": "File uploaded successfully (basic processing)",
            "document_id": pdf_doc.id,
            "uuid": pdf_doc.uuid,
            "total_pages": total_pages,
            "file_size_bytes": file_size,
            "layout_preservation": False,
            "enhanced_features": []
        }

@router.post("/analyze-semantic/{document_id}")
async def analyze_semantic_structure(
    document_id: int, 
    db: Session = Depends(get_db)
):
    """Run comprehensive semantic analysis on document"""
    document = db.query(PDFDocument).filter(PDFDocument.id == document_id).first()
    if not document:
        raise HTTPException(404, "Document not found")
    
    try:
        # Initialize semantic analyzer
        analyzer = SemanticAnalyzer()
        
        # Analyze document structure
        document_structures = analyzer.analyze_document_structure(document.file_path)
        
        # Update document with analysis results
        document.text_density_score = 0.8  # Placeholder
        document.layout_complexity_score = 0.7  # Placeholder
        document.academic_term_count = sum(len(structures) for structures in document_structures.values())
        document.analysis_completed = True
        
        db.commit()
        
        # Store semantic structures in database
        pages = db.query(PDFPage).filter(PDFPage.document_id == document_id).all()
        
        for page in pages:
            # Update page with semantic structures
            page.sentences = document_structures.get("sentences", [])
            page.paragraphs = document_structures.get("paragraphs", [])
            page.sections = document_structures.get("sections", [])
            page.chapters = document_structures.get("chapters", [])
            
            # Calculate page metrics
            page.sentence_count = len(page.sentences)
            page.paragraph_count = len(page.paragraphs)
            page.word_count = sum(s.get("word_count", 0) for s in page.sentences)
            
            # Calculate complexity score
            if page.sentences:
                page.complexity_score = sum(s.get("complexity_score", 0) for s in page.sentences) / len(page.sentences)
            
            db.commit()
        
        return {
            "message": "Semantic analysis completed",
            "document_id": document_id,
            "structures_found": {
                "sentences": len(document_structures.get("sentences", [])),
                "paragraphs": len(document_structures.get("paragraphs", [])),
                "sections": len(document_structures.get("sections", [])),
                "chapters": len(document_structures.get("chapters", [])),
                "tables": len(document_structures.get("tables", [])),
                "columns": len(document_structures.get("columns", []))
            }
        }
        
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")

@router.get("/semantic-structure/{document_id}")
async def get_semantic_structure(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get semantic structure analysis results"""
    document = db.query(PDFDocument).filter(PDFDocument.id == document_id).first()
    if not document:
        raise HTTPException(404, "Document not found")
    
    if not document.analysis_completed:
        raise HTTPException(400, "Semantic analysis not completed")
    
    pages = db.query(PDFPage).filter(PDFPage.document_id == document_id).all()
    
    structure_summary = {
        "document_id": document_id,
        "total_pages": document.total_pages,
        "analysis_completed": document.analysis_completed,
        "pages": []
    }
    
    for page in pages:
        page_structure = {
            "page_number": page.page_number,
            "sentences": page.sentences,
            "paragraphs": page.paragraphs,
            "sections": page.sections,
            "chapters": page.chapters,
            "complexity_score": page.complexity_score,
            "word_count": page.word_count,
            "sentence_count": page.sentence_count,
            "paragraph_count": page.paragraph_count
        }
        structure_summary["pages"].append(page_structure)
    
    return structure_summary

@router.post("/translate-sample/{document_id}/page/{page_number}")
async def translate_sample_page(
    document_id: int,
    page_number: int,
    db: Session = Depends(get_db)
):
    """Translate a sample page for testing"""
    document = db.query(PDFDocument).filter(PDFDocument.id == document_id).first()
    if not document:
        raise HTTPException(404, "Document not found")
    
    page = db.query(PDFPage).filter(
        PDFPage.document_id == document_id,
        PDFPage.page_number == page_number
    ).first()
    
    if not page:
        raise HTTPException(404, "Page not found")
    
    try:
        # Initialize translation service
        translation_service = TranslationService()
        
        # Translate the page
        translated_page = translation_service.translate_page(db, page.id)
        
        # Create sample translation record
        sample_translation = SampleTranslation(
            document_id=document_id,
            page_id=page.id,
            sample_type="page",
            sample_text=page.original_text,
            translated_text=translated_page.translated_text,
            cost_estimate=translated_page.cost_estimate,
            processing_time=translated_page.translation_time,
            quality_score=0.9  # Placeholder
        )
        
        db.add(sample_translation)
        db.commit()
        
        return {
            "message": "Sample page translation completed",
            "document_id": document_id,
            "page_number": page_number,
            "original_text": page.original_text[:500] + "..." if len(page.original_text) > 500 else page.original_text,
            "translated_text": translated_page.translated_text[:500] + "..." if len(translated_page.translated_text) > 500 else translated_page.translated_text,
            "cost_estimate": translated_page.cost_estimate,
            "processing_time": translated_page.translation_time,
            "quality_score": 0.9,
            "sample_id": sample_translation.id
        }
        
    except Exception as e:
        raise HTTPException(500, f"Sample translation failed: {str(e)}")

@router.post("/translate-sample/{document_id}/paragraph/{paragraph_index}")
async def translate_sample_paragraph(
    document_id: int,
    paragraph_index: int,
    page_number: int,
    db: Session = Depends(get_db)
):
    """Translate a sample paragraph for testing"""
    document = db.query(PDFDocument).filter(PDFDocument.id == document_id).first()
    if not document:
        raise HTTPException(404, "Document not found")
    
    page = db.query(PDFPage).filter(
        PDFPage.document_id == document_id,
        PDFPage.page_number == page_number
    ).first()
    
    if not page:
        raise HTTPException(404, "Page not found")
    
    if not page.paragraphs or paragraph_index >= len(page.paragraphs):
        raise HTTPException(404, "Paragraph not found")
    
    try:
        paragraph_data = page.paragraphs[paragraph_index]
        paragraph_text = paragraph_data.get("text", "")
        
        if not paragraph_text:
            raise HTTPException(400, "Paragraph text is empty")
        
        # Initialize translation service
        translation_service = TranslationService()
        
        # Translate the paragraph
        translated_text = translation_service.translate_text(paragraph_text)
        cost_estimate = translation_service.estimate_cost(paragraph_text)
        
        # Create sample translation record
        sample_translation = SampleTranslation(
            document_id=document_id,
            page_id=page.id,
            sample_type="paragraph",
            sample_text=paragraph_text,
            translated_text=translated_text,
            cost_estimate=cost_estimate,
            processing_time=0.5,  # Placeholder
            quality_score=0.9  # Placeholder
        )
        
        db.add(sample_translation)
        db.commit()
        
        return {
            "message": "Sample paragraph translation completed",
            "document_id": document_id,
            "page_number": page_number,
            "paragraph_index": paragraph_index,
            "original_text": paragraph_text,
            "translated_text": translated_text,
            "cost_estimate": cost_estimate,
            "processing_time": 0.5,
            "quality_score": 0.9,
            "sample_id": sample_translation.id
        }
        
    except Exception as e:
        raise HTTPException(500, f"Sample paragraph translation failed: {str(e)}")

@router.get("/sample-translations/{document_id}")
async def get_sample_translations(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get all sample translations for a document"""
    document = db.query(PDFDocument).filter(PDFDocument.id == document_id).first()
    if not document:
        raise HTTPException(404, "Document not found")
    
    sample_translations = db.query(SampleTranslation).filter(
        SampleTranslation.document_id == document_id
    ).all()
    
    return {
        "document_id": document_id,
        "sample_translations": [
            {
                "id": sample.id,
                "sample_type": sample.sample_type,
                "sample_text": sample.sample_text[:200] + "..." if len(sample.sample_text) > 200 else sample.sample_text,
                "translated_text": sample.translated_text[:200] + "..." if len(sample.translated_text) > 200 else sample.translated_text,
                "cost_estimate": sample.cost_estimate,
                "processing_time": sample.processing_time,
                "quality_score": sample.quality_score,
                "user_approved": sample.user_approved,
                "created_at": sample.created_at
            }
            for sample in sample_translations
        ]
    }

@router.post("/approve-sample/{sample_id}")
async def approve_sample_translation(
    sample_id: int,
    feedback: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Approve a sample translation"""
    sample = db.query(SampleTranslation).filter(SampleTranslation.id == sample_id).first()
    if not sample:
        raise HTTPException(404, "Sample translation not found")
    
    sample.user_approved = True
    if feedback:
        sample.user_feedback = feedback
    
    db.commit()
    
    return {
        "message": "Sample translation approved",
        "sample_id": sample_id,
        "approved": True
    }

@router.get("/preserve-format/{page_id}")
async def get_format_preservation_options(
    page_id: int,
    db: Session = Depends(get_db)
):
    """Get format preservation options for a page"""
    page = db.query(PDFPage).filter(PDFPage.id == page_id).first()
    if not page:
        raise HTTPException(404, "Page not found")
    
    # Analyze format preservation options
    format_options = {
        "page_id": page_id,
        "page_number": page.page_number,
        "layout_type": "text",  # Placeholder
        "column_count": 1,  # Placeholder
        "has_tables": False,  # Placeholder
        "has_images": False,  # Placeholder
        "formatting_options": {
            "preserve_columns": True,
            "preserve_tables": True,
            "preserve_fonts": True,
            "preserve_spacing": True
        },
        "estimated_preservation_cost": 0.05  # Placeholder
    }
    
    return format_options

@router.post("/gradual-translate/{document_id}")
async def start_gradual_translation(
    document_id: int,
    strategy: str = "semantic",
    selected_pages: Optional[List[int]] = None,
    db: Session = Depends(get_db)
):
    """Start gradual translation with user control"""
    document = db.query(PDFDocument).filter(PDFDocument.id == document_id).first()
    if not document:
        raise HTTPException(404, "Document not found")
    
    try:
        # Create translation job
        job = TranslationJob(
            document_id=document_id,
            job_type="gradual",
            status="pending",
            total_pages=len(selected_pages) if selected_pages else document.total_pages
        )
        
        db.add(job)
        db.commit()
        
        # Start celery task for gradual translation
        task = process_document_translation.delay(document_id, job.id)
        job.celery_task_id = task.id
        job.status = "started"
        job.started_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "message": "Gradual translation started",
            "document_id": document_id,
            "job_id": job.id,
            "task_id": task.id,
            "strategy": strategy,
            "selected_pages": selected_pages,
            "total_pages": job.total_pages
        }
        
    except Exception as e:
        raise HTTPException(500, f"Failed to start gradual translation: {str(e)}")

@router.get("/translation-progress/{document_id}")
async def get_translation_progress(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get real-time translation progress"""
    document = db.query(PDFDocument).filter(PDFDocument.id == document_id).first()
    if not document:
        raise HTTPException(404, "Document not found")
    
    # Get latest translation job
    job = db.query(TranslationJob).filter(
        TranslationJob.document_id == document_id
    ).order_by(TranslationJob.created_at.desc()).first()
    
    if not job:
        return {
            "document_id": document_id,
            "status": "no_job",
            "progress": 0,
            "message": "No translation job found"
        }
    
    # Calculate progress
    progress_percentage = (job.pages_processed / job.total_pages * 100) if job.total_pages > 0 else 0
    
    return {
        "document_id": document_id,
        "job_id": job.id,
        "status": job.status,
        "progress_percentage": progress_percentage,
        "pages_processed": job.pages_processed,
        "total_pages": job.total_pages,
        "estimated_cost": job.estimated_cost,
        "actual_cost": job.actual_cost,
        "started_at": job.started_at,
        "completed_at": job.completed_at
    }
