# Enhanced API Endpoints for Semantic PDF Translation
# backend/app/api/endpoints/enhanced_documents.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
import os
import uuid
import logging
import traceback
from datetime import datetime

from app.core.database import get_db
from app.core.config import settings
from app.models.models import PDFDocument, PDFPage, SemanticStructure, SampleTranslation, TranslationJob
from app.models.user_models import User
from app.services.suggestions_service import SuggestionsService
from app.services.glossary_service import GlossaryEnforcementService
from app.services.quality_service import QualityScoringService
from app.services.comments_service import CommentsService
from app.services.presence_service import PresenceService

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload-enhanced", response_model=dict)
async def upload_pdf_enhanced(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload PDF document with enhanced processing and layout preservation"""
    
    # Log upload attempt
    safe_size = getattr(file, "size", None)
    logger.info(f"Enhanced upload attempt started: filename={file.filename}, content_type={file.content_type}, size={safe_size}")
    
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
        
        # Try enhanced processing first
        try:
            logger.info("Attempting enhanced PDF processing")
            enhanced_service = EnhancedPDFService()
            pdf_doc = enhanced_service.save_enhanced_pdf_to_db(db, filename, file.filename, file_path)
            
            logger.info(f"Enhanced processing successful: document_id={pdf_doc.id}")
            
            return {
                "message": "File uploaded successfully with enhanced processing",
                "document_id": pdf_doc.id,
                "uuid": pdf_doc.uuid,
                "total_pages": pdf_doc.total_pages,
                "file_size_bytes": actual_size,
                "layout_preservation": True,
                "enhanced_features": ["layout_analysis", "table_detection", "format_preservation"]
            }
            
        except Exception as e:
            # Fallback to basic processing
            logger.warning(f"Enhanced processing failed, falling back to basic: {str(e)}", exc_info=True)
            
            try:
                pdf_doc = PDFDocument(
                    filename=filename,
                    original_filename=file.filename,
                    file_path=file_path,
                    file_size_bytes=actual_size,
                    status="uploaded"
                )
                
                db.add(pdf_doc)
                db.commit()
                db.refresh(pdf_doc)
                
                logger.info(f"Basic document saved to database: id={pdf_doc.id}, uuid={pdf_doc.uuid}")
                
                # Extract pages and basic info
                try:
                    total_pages = PDFService.extract_and_save_pages(db, pdf_doc.id, file_path)
                    logger.info(f"Pages extracted successfully: {total_pages} pages")
                except Exception as page_error:
                    logger.warning(f"Failed to extract pages: {str(page_error)}", exc_info=True)
                    total_pages = 0
                
                # Update document with page count
                pdf_doc.total_pages = total_pages
                db.commit()
                
                logger.info(f"Basic upload completed successfully: document_id={pdf_doc.id}")
                
                return {
                    "message": "File uploaded successfully (basic processing)",
                    "document_id": pdf_doc.id,
                    "uuid": pdf_doc.uuid,
                    "total_pages": total_pages,
                    "file_size_bytes": actual_size,
                    "layout_preservation": False,
                    "enhanced_features": [],
                    "fallback_reason": str(e)
                }
                
            except Exception as basic_error:
                error_msg = f"Both enhanced and basic processing failed: {str(basic_error)}"
                logger.error(error_msg, exc_info=True)
                # Clean up saved file
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        logger.debug(f"Cleaned up file after processing error: {file_path}")
                except:
                    pass
                raise HTTPException(status_code=500, detail=error_msg)
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any unexpected errors
        error_msg = f"Unexpected error during enhanced upload: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error during enhanced upload")

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start gradual translation with user control"""
    document = db.query(PDFDocument).filter(PDFDocument.id == document_id).first()
    if not document:
        raise HTTPException(404, "Document not found")
    
    try:
        # Start celery task for gradual translation (task will create its own job)
        task = process_document_translation.delay(document_id)

        return {
            "message": "Gradual translation started",
            "document_id": document_id,
            "task_id": task.id,
            "strategy": strategy,
            "selected_pages": selected_pages,
            "total_pages": document.total_pages
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
        # Even without a job, provide page-level rollups
        pages = db.query(PDFPage).filter(PDFPage.document_id == document_id).all()
        tokens_in_total = sum(int(getattr(p, 'tokens_in', 0) or 0) for p in pages)
        tokens_out_total = sum(int(getattr(p, 'tokens_out', 0) or 0) for p in pages)
        pages_cost_total = float(sum((p.cost_estimate or 0.0) for p in pages))
        return {
            "document_id": document_id,
            "status": "no_job",
            "progress": 0,
            "message": "No translation job found",
            "tokens_in_total": tokens_in_total,
            "tokens_out_total": tokens_out_total,
            "pages_cost_total": pages_cost_total,
        }
    
    # Calculate progress
    progress_percentage = (job.pages_processed / job.total_pages * 100) if job.total_pages > 0 else 0
    # Page-level rollups
    pages = db.query(PDFPage).filter(PDFPage.document_id == document_id).all()
    tokens_in_total = sum(int(getattr(p, 'tokens_in', 0) or 0) for p in pages)
    tokens_out_total = sum(int(getattr(p, 'tokens_out', 0) or 0) for p in pages)
    pages_cost_total = float(sum((p.cost_estimate or 0.0) for p in pages))

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
        "completed_at": job.completed_at,
        "tokens_in_total": tokens_in_total,
        "tokens_out_total": tokens_out_total,
        "pages_cost_total": pages_cost_total,
    }

@router.get("/export/{document_id}")
async def export_document_markdown(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Export translated document as a simple Markdown concatenation (skeleton)."""
    document = db.query(PDFDocument).filter(PDFDocument.id == document_id).first()
    if not document:
        raise HTTPException(404, "Document not found")

    pages = db.query(PDFPage).filter(PDFPage.document_id == document_id).order_by(PDFPage.page_number.asc()).all()
    if not pages:
        raise HTTPException(400, "No pages found for document")

    parts = []
    for p in pages:
        parts.append(f"\n\n# Page {p.page_number}\n\n{(p.translated_text or '').strip()}")
    md = "".join(parts).strip() or "# Empty translation"
    return {"document_id": document_id, "format": "markdown", "content": md}


@router.post("/documents/{document_id}/pages/{page_number}/translate")
async def translate_page_lazy(
    document_id: int,
    page_number: int,
    provider: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start lazy translation for a specific page"""
    try:
        # Get the page
        page = db.query(PDFPage).filter(
            PDFPage.document_id == document_id,
            PDFPage.page_number == page_number
        ).first()
        
        if not page:
            raise HTTPException(404, f"Page {page_number} not found in document {document_id}")
        
        # Check if already translated
        if page.translation_status == "completed":
            return {
                "job_id": f"page_{page.id}_already_completed",
                "status": "completed",
                "message": "Page already translated"
            }
        
        # Update status to processing
        page.translation_status = "processing"
        db.commit()
        
        # Start translation job
        job_id = f"page_{page.id}_{int(datetime.utcnow().timestamp())}"
        
        # For now, we'll do synchronous translation
        # In production, this should be queued as a background task
        try:
            translation_service = TranslationService()
            translated_text = translation_service.translate_text(
                page.original_text, 
                "en", 
                "fa", 
                provider
            )
            
            page.translated_text = translated_text
            page.translation_status = "completed"
            page.translation_model = translation_service.provider_router.get(provider).name
            page.cost_estimate = translation_service.estimate_cost(page.original_text, "en", "fa", provider)
            
            db.commit()
            
            return {
                "job_id": job_id,
                "status": "completed",
                "message": "Translation completed successfully"
            }
            
        except Exception as e:
            page.translation_status = "failed"
            db.commit()
            raise HTTPException(500, f"Translation failed: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in lazy translation: {e}")
        raise HTTPException(500, "Internal server error")


@router.get("/documents/{document_id}/pages/{page_number}")
async def get_page_with_translation(
    document_id: int,
    page_number: int,
    db: Session = Depends(get_db)
):
    """Get page details including translation status and provider info"""
    try:
        page = db.query(PDFPage).filter(
            PDFPage.document_id == document_id,
            PDFPage.page_number == page_number
        ).first()
        
        if not page:
            raise HTTPException(404, f"Page {page_number} not found in document {document_id}")
        
        return {
            "page_id": page.id,
            "page_number": page.page_number,
            "document_id": page.document_id,
            "status": page.translation_status,
            "source_text": page.original_text,
            "translated_text": page.translated_text,
            "provider": getattr(page, 'translation_model', 'unknown'),
            "cost_estimate": getattr(page, 'cost_estimate', 0.0),
            "translation_time": getattr(page, 'translation_time', None),
            "quality_score": getattr(page, 'quality_score', None),
            "tokens_used": getattr(page, 'tokens_used', None),
            "created_at": page.created_at.isoformat() if page.created_at else None,
            "updated_at": page.updated_at.isoformat() if page.updated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting page details: {e}")
        raise HTTPException(500, "Internal server error")


@router.get("/documents/{document_id}/pages/{page_number}/suggestions")
async def get_page_suggestions(
    document_id: int,
    page_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get suggestions for a specific page"""
    try:
        page = db.query(PDFPage).filter(
            PDFPage.document_id == document_id,
            PDFPage.page_number == page_number
        ).first()
        
        if not page:
            raise HTTPException(404, f"Page {page_number} not found in document {document_id}")
        
        # For now, return empty suggestions
        # In the future, this will query the suggestions table
        return {
            "page_id": page.id,
            "page_number": page.page_number,
            "suggestions": [],
            "total_count": 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting page suggestions: {e}")
        raise HTTPException(500, "Internal server error")


@router.post("/suggestions/{suggestion_id}/accept")
async def accept_suggestion(
    suggestion_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Accept a suggestion and apply it to the page"""
    try:
        # For now, return a placeholder response
        # In the future, this will update the page with the accepted suggestion
        return {
            "suggestion_id": suggestion_id,
            "status": "accepted",
            "message": "Suggestion accepted successfully",
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error accepting suggestion: {e}")
        raise HTTPException(500, "Internal server error")


@router.post("/suggestions/{suggestion_id}/reject")
async def reject_suggestion(
    suggestion_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reject a suggestion"""
    try:
        # For now, return a placeholder response
        # In the future, this will mark the suggestion as rejected
        return {
            "suggestion_id": suggestion_id,
            "status": "rejected",
            "message": "Suggestion rejected",
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error rejecting suggestion: {e}")
        raise HTTPException(500, "Internal server error")


@router.post("/documents/{document_id}/pages/{page_number}/enforce-glossary")
async def enforce_glossary_on_page(
    document_id: int,
    page_number: int,
    strict_mode: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enforce glossary terms on a specific page"""
    try:
        page = db.query(PDFPage).filter(
            PDFPage.document_id == document_id,
            PDFPage.page_number == page_number
        ).first()
        
        if not page:
            raise HTTPException(404, f"Page {page_number} not found in document {document_id}")
        
        glossary_service = GlossaryEnforcementService(db)
        result = await glossary_service.enforce_glossary_on_page(
            page.id, current_user.id, strict_mode
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enforcing glossary on page: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/documents/{document_id}/enforce-glossary")
async def batch_enforce_glossary(
    document_id: int,
    page_numbers: Optional[List[int]] = None,
    strict_mode: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enforce glossary terms on multiple pages"""
    try:
        glossary_service = GlossaryEnforcementService(db)
        result = await glossary_service.batch_enforce_glossary(
            document_id, current_user.id, page_numbers, strict_mode
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error batch enforcing glossary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/documents/{document_id}/pages/{page_number}/quality-score")
async def get_page_quality_score(
    document_id: int,
    page_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get quality score for a specific page"""
    try:
        page = db.query(PDFPage).filter(
            PDFPage.document_id == document_id,
            PDFPage.page_number == page_number
        ).first()
        
        if not page:
            raise HTTPException(404, f"Page {page_number} not found in document {document_id}")
        
        quality_service = QualityScoringService(db)
        result = await quality_service.score_page(page.id, current_user.id)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting page quality score: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/documents/{document_id}/quality-score")
async def get_document_quality_score(
    document_id: int,
    page_numbers: Optional[List[int]] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get quality scores for all pages in a document"""
    try:
        quality_service = QualityScoringService(db)
        result = await quality_service.score_document(
            document_id, current_user.id, page_numbers
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting document quality score: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/documents/{document_id}/quality-trends")
async def get_quality_trends(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get quality trends over time for a document"""
    try:
        quality_service = QualityScoringService(db)
        result = await quality_service.get_quality_trends(document_id, current_user.id)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting quality trends: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/glossary/statistics")
async def get_glossary_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get statistics about user's glossary"""
    try:
        glossary_service = GlossaryEnforcementService(db)
        result = await glossary_service.get_glossary_statistics(current_user.id)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting glossary statistics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/glossary/suggest-terms")
async def suggest_glossary_terms(
    text: str,
    min_frequency: int = 2,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Suggest potential glossary terms from text"""
    try:
        glossary_service = GlossaryEnforcementService(db)
        suggestions = await glossary_service.suggest_glossary_terms(
            text, current_user.id, min_frequency
        )
        
        return {
            "suggestions": suggestions,
            "total_count": len(suggestions),
            "min_frequency": min_frequency
        }
        
    except Exception as e:
        logger.error(f"Error suggesting glossary terms: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Comments endpoints
@router.post("/documents/{document_id}/pages/{page_number}/comments")
async def create_comment(
    document_id: int,
    page_number: int,
    comment_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new comment on a page"""
    try:
        page = db.query(PDFPage).filter(
            PDFPage.document_id == document_id,
            PDFPage.page_number == page_number
        ).first()
        
        if not page:
            raise HTTPException(404, f"Page {page_number} not found in document {document_id}")
        
        comments_service = CommentsService(db)
        comment = await comments_service.create_comment(
            page.id,
            comment_data.get("segment_id", ""),
            comment_data.get("text", ""),
            current_user.id,
            comment_data.get("parent_comment_id")
        )
        
        return comment
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating comment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/documents/{document_id}/pages/{page_number}/comments")
async def get_page_comments(
    document_id: int,
    page_number: int,
    segment_id: Optional[str] = None,
    include_replies: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all comments for a page"""
    try:
        page = db.query(PDFPage).filter(
            PDFPage.document_id == document_id,
            PDFPage.page_number == page_number
        ).first()
        
        if not page:
            raise HTTPException(404, f"Page {page_number} not found in document {document_id}")
        
        comments_service = CommentsService(db)
        comments = await comments_service.get_comments_for_page(
            page.id, segment_id, include_replies
        )
        
        return {
            "page_id": page.id,
            "page_number": page_number,
            "comments": comments,
            "total_count": len(comments)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting page comments: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/comments/{comment_id}")
async def update_comment(
    comment_id: str,
    comment_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a comment"""
    try:
        comments_service = CommentsService(db)
        result = await comments_service.update_comment(
            comment_id,
            comment_data.get("text", ""),
            current_user.id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error updating comment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a comment"""
    try:
        comments_service = CommentsService(db)
        result = await comments_service.delete_comment(comment_id, current_user.id)
        
        return result
        
    except Exception as e:
        logger.error(f"Error deleting comment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/comments/{comment_id}/resolve")
async def resolve_comment(
    comment_id: str,
    resolution_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a comment as resolved"""
    try:
        comments_service = CommentsService(db)
        result = await comments_service.resolve_comment(
            comment_id,
            current_user.id,
            resolution_data.get("resolution_note")
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error resolving comment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/comments/{comment_id}/reactions")
async def add_reaction(
    comment_id: str,
    reaction_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a reaction to a comment"""
    try:
        comments_service = CommentsService(db)
        result = await comments_service.add_reaction(
            comment_id,
            reaction_data.get("reaction", ""),
            current_user.id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error adding reaction: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/comments/{comment_id}/reactions/{reaction}")
async def remove_reaction(
    comment_id: str,
    reaction: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a reaction from a comment"""
    try:
        comments_service = CommentsService(db)
        result = await comments_service.remove_reaction(
            comment_id,
            reaction,
            current_user.id
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error removing reaction: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Presence endpoints
@router.get("/documents/{document_id}/pages/{page_number}/presence")
async def get_page_presence(
    document_id: int,
    page_number: int
):
    """Get current presence information for a page"""
    try:
        presence_service = PresenceService()
        presence = await presence_service.get_page_presence(page_number)
        
        return presence
        
    except Exception as e:
        logger.error(f"Error getting page presence: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/documents/{document_id}/pages/{page_number}/presence/join")
async def join_page(
    document_id: int,
    page_number: int,
    user_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """User joins a page"""
    try:
        presence_service = PresenceService()
        result = await presence_service.join_page(
            page_number,
            current_user.id,
            user_data
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error joining page: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/documents/{document_id}/pages/{page_number}/presence/leave")
async def leave_page(
    document_id: int,
    page_number: int,
    current_user: User = Depends(get_current_user)
):
    """User leaves a page"""
    try:
        presence_service = PresenceService()
        result = await presence_service.leave_page(page_number, current_user.id)
        
        return result
        
    except Exception as e:
        logger.error(f"Error leaving page: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/documents/{document_id}/pages/{page_number}/presence/cursor")
async def update_cursor_position(
    document_id: int,
    page_number: int,
    cursor_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Update user's cursor position"""
    try:
        presence_service = PresenceService()
        result = await presence_service.update_cursor_position(
            page_number,
            current_user.id,
            cursor_data
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error updating cursor position: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/documents/{document_id}/pages/{page_number}/presence/selection")
async def update_selection_range(
    document_id: int,
    page_number: int,
    selection_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Update user's text selection range"""
    try:
        presence_service = PresenceService()
        result = await presence_service.update_selection_range(
            page_number,
            current_user.id,
            selection_data
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error updating selection range: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/documents/{document_id}/pages/{page_number}/locks")
async def acquire_soft_lock(
    document_id: int,
    page_number: int,
    lock_data: Dict[str, Any],
    current_user: User = Depends(get_current_user)
):
    """Acquire a soft lock on a resource"""
    try:
        presence_service = PresenceService()
        result = await presence_service.acquire_soft_lock(
            page_number,
            current_user.id,
            lock_data.get("resource", ""),
            lock_data.get("lock_type", "edit")
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error acquiring soft lock: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/documents/{document_id}/pages/{page_number}/locks/{resource}")
async def release_soft_lock(
    document_id: int,
    page_number: int,
    resource: str,
    current_user: User = Depends(get_current_user)
):
    """Release a soft lock on a resource"""
    try:
        presence_service = PresenceService()
        result = await presence_service.release_soft_lock(
            page_number,
            current_user.id,
            resource
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error releasing soft lock: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/documents/{document_id}/pages/{page_number}/locks/{resource}/renew")
async def renew_soft_lock(
    document_id: int,
    page_number: int,
    resource: str,
    current_user: User = Depends(get_current_user)
):
    """Renew a soft lock to extend its expiration"""
    try:
        presence_service = PresenceService()
        result = await presence_service.renew_soft_lock(
            page_number,
            current_user.id,
            resource
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error renewing soft lock: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
