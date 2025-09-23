from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional

from app.core.database import get_db
from app.models.models import PDFPage, SemanticStructure

router = APIRouter()


def _page_to_dict(page: PDFPage) -> Dict[str, Any]:
    blocks: List[Dict[str, Any]] = []
    # Map SemanticStructure rows to generic blocks/segments structure
    structures = sorted(page.semantic_structures or [], key=lambda s: (s.structure_type or '', s.structure_index or 0))
    for s in structures:
        blocks.append({
            "id": s.id,
            "type": s.structure_type,
            "bbox": s.layout_position or {},
            "text": s.original_text,
            "segments": [
                {
                    "id": s.id,  # Single segment per structure for now; can expand later
                    "bbox": s.layout_position or {},
                    "text": s.original_text,
                    "translated_text": s.translated_text,
                }
            ],
        })

    return {
        "id": page.id,
        "document_id": page.document_id,
        "page_number": page.page_number,
        "blocks": blocks,
    }


@router.get("/{page_id}", response_model=dict)
def get_page_detail(page_id: int, db: Session = Depends(get_db)):
    page = db.query(PDFPage).filter(PDFPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return _page_to_dict(page)


@router.patch("/{page_id}", response_model=dict)
def update_page_translation(page_id: int, body: Dict[str, Any], db: Session = Depends(get_db)):
    page = db.query(PDFPage).filter(PDFPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")

    translated_text: Optional[str] = body.get("translated_text")
    segments: Optional[List[Dict[str, Any]]] = body.get("segments")

    if translated_text is None and not segments:
        raise HTTPException(status_code=400, detail="No changes provided")

    if translated_text is not None:
        page.translated_text = translated_text

    if segments:
        # Apply updates per segment id → translated_text
        index_by_id = {s.id: s for s in (page.semantic_structures or [])}
        for seg in segments:
            seg_id = seg.get("id")
            seg_text = seg.get("translated_text")
            if seg_id in index_by_id and seg_text is not None:
                index_by_id[seg_id].translated_text = seg_text

    db.add(page)
    db.commit()
    return {"message": "updated", "page_id": page.id}


@router.post("/{page_id}/approve", response_model=dict)
def approve_page(page_id: int, db: Session = Depends(get_db)):
    page = db.query(PDFPage).filter(PDFPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    page.translation_status = "approved"
    db.add(page)
    db.commit()
    return {"message": "approved", "page_id": page.id}


@router.post("/{page_id}/reject", response_model=dict)
def reject_page(page_id: int, db: Session = Depends(get_db)):
    page = db.query(PDFPage).filter(PDFPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    page.translation_status = "rejected"
    db.add(page)
    db.commit()
    return {"message": "rejected", "page_id": page.id}

