# Backend Mastery: FastAPI, Services, and Data

Overview of our backend stack and how to extend it safely and idiomatically.

## Topology
- Entry: `backend/app/main.py`
- Routers: `backend/app/api/endpoints/`
- Services: `backend/app/services/`
- Models: `backend/app/models/models.py`
- Core: `backend/app/core/`

## Run Locally
- `cd backend && pip install -r requirements.txt`
- `uvicorn app.main:app --reload`
- Docs: `http://localhost:8000/docs`

## Services You’ll Use
- `pdf_service.py`: extract text, save pages, layout info
- `translation_service.py`: OpenAI translation, cost estimate, validation
- `chunker.py`: token-aware segmentation

## Add an Endpoint (pattern)
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.translation_service import TranslationService

router = APIRouter(prefix="/translate", tags=["translate"])

@router.post("/quick")
def quick_translate(text: str, db: Session = Depends(get_db)):
    if not text.strip():
        raise HTTPException(400, "empty input")
    return TranslationService().translate_with_quality_check(text)
```

## Design Guidelines
- Keep endpoints thin; put logic in services
- Pass dependencies (DB, config); avoid globals
- Make operations idempotent; mark statuses predictably

## Testing
```bash
cd backend && python -m pytest -v
```
Simple smoke test:
```python
def test_cost_estimate():
    from app.services.translation_service import TranslationService
    assert TranslationService().estimate_cost("hello") >= 0
```

## Next
- Provider routing: `learn/04-translation-providers-llm-routing.md`
- Collab & realtime: `learn/03-realtime-collab-crdt-yjs.md`

