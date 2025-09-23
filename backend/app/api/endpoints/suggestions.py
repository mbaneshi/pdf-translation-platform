# Suggestions API endpoints
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.core.database import get_db
from app.models.user_models import User
from app.api.endpoints.auth import get_current_user
from app.services.suggestions_service import SuggestionsService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/documents/{document_id}/pages/{page_number}/suggestions")
async def get_page_suggestions(
    document_id: int,
    page_number: int,
    status: Optional[str] = Query(None, description="Filter by suggestion status"),
    suggestion_type: Optional[str] = Query(None, description="Filter by suggestion type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get suggestions for a specific page"""
    try:
        suggestions_service = SuggestionsService(db)
        suggestions = await suggestions_service.get_page_suggestions(
            document_id, page_number, status, suggestion_type
        )
        
        return {
            "page_id": f"{document_id}_{page_number}",
            "page_number": page_number,
            "suggestions": suggestions,
            "total_count": len(suggestions)
        }
        
    except Exception as e:
        logger.error(f"Error getting page suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get suggestions")


@router.post("/suggestions")
async def create_suggestion(
    suggestion_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new suggestion"""
    try:
        suggestions_service = SuggestionsService(db)
        suggestion = await suggestions_service.create_suggestion(
            suggestion_data, current_user.id
        )
        
        return {
            "suggestion_id": suggestion["id"],
            "status": "created",
            "message": "Suggestion created successfully",
            "suggestion": suggestion
        }
        
    except Exception as e:
        logger.error(f"Error creating suggestion: {e}")
        raise HTTPException(status_code=500, detail="Failed to create suggestion")


@router.post("/suggestions/{suggestion_id}/accept")
async def accept_suggestion(
    suggestion_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Accept a suggestion and apply it to the page"""
    try:
        suggestions_service = SuggestionsService(db)
        result = await suggestions_service.accept_suggestion(
            suggestion_id, current_user.id
        )
        
        return {
            "suggestion_id": suggestion_id,
            "status": "accepted",
            "message": "Suggestion accepted successfully",
            "updated_at": datetime.utcnow().isoformat(),
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error accepting suggestion: {e}")
        raise HTTPException(status_code=500, detail="Failed to accept suggestion")


@router.post("/suggestions/{suggestion_id}/reject")
async def reject_suggestion(
    suggestion_id: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reject a suggestion"""
    try:
        suggestions_service = SuggestionsService(db)
        await suggestions_service.reject_suggestion(
            suggestion_id, current_user.id, reason
        )
        
        return {
            "suggestion_id": suggestion_id,
            "status": "rejected",
            "message": "Suggestion rejected",
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error rejecting suggestion: {e}")
        raise HTTPException(status_code=500, detail="Failed to reject suggestion")


@router.get("/suggestions/{suggestion_id}")
async def get_suggestion(
    suggestion_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific suggestion by ID"""
    try:
        suggestions_service = SuggestionsService(db)
        suggestion = await suggestions_service.get_suggestion(suggestion_id)
        
        if not suggestion:
            raise HTTPException(status_code=404, detail="Suggestion not found")
        
        return suggestion
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting suggestion: {e}")
        raise HTTPException(status_code=500, detail="Failed to get suggestion")


@router.get("/documents/{document_id}/suggestions")
async def get_document_suggestions(
    document_id: int,
    status: Optional[str] = Query(None, description="Filter by suggestion status"),
    suggestion_type: Optional[str] = Query(None, description="Filter by suggestion type"),
    limit: int = Query(50, description="Number of suggestions to return"),
    offset: int = Query(0, description="Number of suggestions to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all suggestions for a document"""
    try:
        suggestions_service = SuggestionsService(db)
        suggestions = await suggestions_service.get_document_suggestions(
            document_id, status, suggestion_type, limit, offset
        )
        
        return {
            "document_id": document_id,
            "suggestions": suggestions,
            "total_count": len(suggestions),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error getting document suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to get document suggestions")


@router.post("/suggestions/batch-accept")
async def batch_accept_suggestions(
    suggestion_ids: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Accept multiple suggestions at once"""
    try:
        suggestions_service = SuggestionsService(db)
        results = await suggestions_service.batch_accept_suggestions(
            suggestion_ids, current_user.id
        )
        
        return {
            "accepted_count": len(results),
            "results": results,
            "message": f"Successfully accepted {len(results)} suggestions"
        }
        
    except Exception as e:
        logger.error(f"Error batch accepting suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to batch accept suggestions")


@router.post("/suggestions/batch-reject")
async def batch_reject_suggestions(
    suggestion_ids: List[str],
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reject multiple suggestions at once"""
    try:
        suggestions_service = SuggestionsService(db)
        results = await suggestions_service.batch_reject_suggestions(
            suggestion_ids, current_user.id, reason
        )
        
        return {
            "rejected_count": len(results),
            "results": results,
            "message": f"Successfully rejected {len(results)} suggestions"
        }
        
    except Exception as e:
        logger.error(f"Error batch rejecting suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to batch reject suggestions")
