# Glossary Management API Endpoints
# backend/app/api/endpoints/glossary.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import logging

from app.core.database import get_db
from app.services.glossary_service import GlossaryService
from app.models.user_models import User
from app.api.endpoints.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for request/response
class GlossaryEntryCreate(BaseModel):
    term: str
    translation: str
    context: Optional[str] = None
    category: Optional[str] = None

class GlossaryEntryUpdate(BaseModel):
    translation: Optional[str] = None
    context: Optional[str] = None
    category: Optional[str] = None
    user_rating: Optional[int] = None

class GlossaryEntryResponse(BaseModel):
    id: int
    uuid: str
    term: str
    translation: str
    context: Optional[str] = None
    category: Optional[str] = None
    usage_count: int
    confidence_score: float
    user_rating: Optional[int] = None
    created_at: str
    last_used: Optional[str] = None

class GlossaryListResponse(BaseModel):
    success: bool
    glossary: List[GlossaryEntryResponse]
    total_count: int
    search_term: Optional[str] = None
    category: Optional[str] = None

class TermExtractionRequest(BaseModel):
    document_text: str

class TermExtractionResponse(BaseModel):
    success: bool
    extracted_terms: List[dict]
    new_terms: List[dict]
    existing_terms: List[str]
    total_extracted: int
    new_count: int

class TranslationConsistencyRequest(BaseModel):
    document_text: str

class TranslationConsistencyResponse(BaseModel):
    success: bool
    consistency_score: float
    matched_terms: List[dict]
    unmatched_terms: List[dict]
    total_terms: int
    matched_count: int
    unmatched_count: int

class GlossaryExportRequest(BaseModel):
    format: str = "json"
    category: Optional[str] = None

class GlossaryImportRequest(BaseModel):
    data: List[dict]

@router.post("/entries", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_glossary_entry(
    entry_data: GlossaryEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new glossary entry"""
    try:
        glossary_service = GlossaryService()
        result = glossary_service.create_glossary_entry(
            user_id=current_user.id,
            term=entry_data.term,
            translation=entry_data.translation,
            context=entry_data.context,
            category=entry_data.category,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create glossary entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create glossary entry"
        )

@router.get("/entries", response_model=GlossaryListResponse)
async def get_user_glossary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all glossary entries for the current user"""
    try:
        glossary_service = GlossaryService()
        result = glossary_service.get_user_glossary(current_user.id, db)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return GlossaryListResponse(
            success=True,
            glossary=[GlossaryEntryResponse(**entry) for entry in result["glossary"]],
            total_count=result["total_count"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get user glossary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve glossary"
        )

@router.get("/entries/search", response_model=GlossaryListResponse)
async def search_glossary_entries(
    search_term: str = Query(..., description="Search term"),
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search glossary entries"""
    try:
        glossary_service = GlossaryService()
        result = glossary_service.search_glossary_entries(
            user_id=current_user.id,
            search_term=search_term,
            category=category,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return GlossaryListResponse(
            success=True,
            glossary=[GlossaryEntryResponse(**entry) for entry in result["glossary"]],
            total_count=result["total_count"],
            search_term=result["search_term"],
            category=result["category"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to search glossary entries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search glossary entries"
        )

@router.get("/entries/category/{category}", response_model=GlossaryListResponse)
async def get_glossary_by_category(
    category: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get glossary entries by category"""
    try:
        glossary_service = GlossaryService()
        result = glossary_service.get_glossary_by_category(
            user_id=current_user.id,
            category=category,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return GlossaryListResponse(
            success=True,
            glossary=[GlossaryEntryResponse(**entry) for entry in result["glossary"]],
            total_count=result["total_count"],
            category=result["category"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get glossary by category: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve glossary by category"
        )

@router.put("/entries/{entry_id}", response_model=dict)
async def update_glossary_entry(
    entry_id: int,
    entry_data: GlossaryEntryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a glossary entry"""
    try:
        glossary_service = GlossaryService()
        result = glossary_service.update_glossary_entry(
            entry_id=entry_id,
            user_id=current_user.id,
            translation=entry_data.translation,
            context=entry_data.context,
            category=entry_data.category,
            user_rating=entry_data.user_rating,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update glossary entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update glossary entry"
        )

@router.delete("/entries/{entry_id}", response_model=dict)
async def delete_glossary_entry(
    entry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a glossary entry"""
    try:
        glossary_service = GlossaryService()
        result = glossary_service.delete_glossary_entry(
            entry_id=entry_id,
            user_id=current_user.id,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete glossary entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete glossary entry"
        )

@router.post("/extract-terms", response_model=TermExtractionResponse)
async def extract_terms_from_document(
    request: TermExtractionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Extract terms from document text"""
    try:
        glossary_service = GlossaryService()
        result = glossary_service.extract_terms_from_document(
            user_id=current_user.id,
            document_text=request.document_text,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return TermExtractionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to extract terms: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract terms from document"
        )

@router.post("/suggest-translations", response_model=dict)
async def suggest_translations(
    terms: List[str],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Suggest translations for terms"""
    try:
        glossary_service = GlossaryService()
        result = glossary_service.suggest_translations(terms, db)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to suggest translations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suggest translations"
        )

@router.post("/check-consistency", response_model=TranslationConsistencyResponse)
async def check_translation_consistency(
    request: TranslationConsistencyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check translation consistency using user's glossary"""
    try:
        glossary_service = GlossaryService()
        result = glossary_service.check_translation_consistency(
            user_id=current_user.id,
            document_text=request.document_text,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return TranslationConsistencyResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check translation consistency: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check translation consistency"
        )

@router.post("/apply-to-translation", response_model=dict)
async def apply_glossary_to_translation(
    original_text: str,
    translated_text: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Apply glossary to translation for consistency"""
    try:
        glossary_service = GlossaryService()
        result = glossary_service.apply_glossary_to_translation(
            user_id=current_user.id,
            original_text=original_text,
            translated_text=translated_text,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to apply glossary to translation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply glossary to translation"
        )

@router.post("/export", response_model=dict)
async def export_glossary(
    request: GlossaryExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export glossary in specified format"""
    try:
        glossary_service = GlossaryService()
        result = glossary_service.export_glossary(
            user_id=current_user.id,
            format=request.format,
            category=request.category,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export glossary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export glossary"
        )

@router.post("/import", response_model=dict)
async def import_glossary(
    request: GlossaryImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import glossary entries from data"""
    try:
        glossary_service = GlossaryService()
        result = glossary_service.import_glossary(
            user_id=current_user.id,
            data=request.data,
            db=db
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import glossary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to import glossary"
        )

@router.get("/consistency-report", response_model=dict)
async def generate_consistency_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate consistency report for user's glossary"""
    try:
        glossary_service = GlossaryService()
        result = glossary_service.generate_consistency_report(current_user.id, db)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate consistency report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate consistency report"
        )
