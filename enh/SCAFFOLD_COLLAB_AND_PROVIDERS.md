# Scaffolding Guide: Collaboration Service and Provider Abstraction

This guide specifies directory structures, interfaces, message schemas, and minimal code sketches to bootstrap a collab service and a pluggable translation provider layer.

## 1) Provider Abstraction

- Paths
  - backend/app/services/providers/__init__.py
  - backend/app/services/providers/base.py
  - backend/app/services/providers/openai_provider.py
  - backend/app/services/providers/argos_provider.py
  - backend/app/services/providers/openai_compatible_provider.py
  - backend/app/services/providers/deep_translator_provider.py
  - backend/app/services/provider_router.py

- Base Interface (Python sketch)
```python
# backend/app/services/providers/base.py
from typing import Iterator, Optional, Dict

class BaseProvider:
    name: str = "base"

    def translate(self, text: str, src: str, tgt: str, options: Optional[Dict] = None) -> str:
        raise NotImplementedError

    def stream_translate(self, text: str, src: str, tgt: str, options: Optional[Dict] = None) -> Iterator[str]:
        """Yield partial chunks for streaming UI."""
        yield self.translate(text, src, tgt, options)
```

- Router (selection policy)
```python
# backend/app/services/provider_router.py
from typing import Optional, Dict
from .providers.base import BaseProvider
from .providers.openai_provider import OpenAIProvider
# from .providers.argos_provider import ArgosProvider

class ProviderRouter:
    def __init__(self, default: str = "openai"):
        self.providers: Dict[str, BaseProvider] = {"openai": OpenAIProvider()}
        self.default = default

    def get(self, name: Optional[str] = None) -> BaseProvider:
        return self.providers.get(name or self.default, self.providers[self.default])
```

- OpenAI Provider (sketch)
```python
# backend/app/services/providers/openai_provider.py
from typing import Iterator, Optional, Dict
from openai import OpenAI
from app.core.config import settings
from .base import BaseProvider

class OpenAIProvider(BaseProvider):
    name = "openai"
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    def translate(self, text: str, src: str, tgt: str, options: Optional[Dict] = None) -> str:
        prompt = f"Translate from {src} to {tgt} keeping meaning and tone.\n\n{text}"
        resp = self.client.completions.create(model=self.model, prompt=prompt, max_tokens=2048, temperature=0.1)
        return resp.choices[0].text.strip()

    def stream_translate(self, text: str, src: str, tgt: str, options: Optional[Dict] = None) -> Iterator[str]:
        # Placeholder: implement with chat/completions stream
        yield self.translate(text, src, tgt, options)
```

- Integration point in `translation_service.py`
```python
# inside TranslationService.__init__
from app.services.provider_router import ProviderRouter
self.provider_router = ProviderRouter(default=settings.TRANSLATION_PROVIDER)

# replace client usage in translate_text
provider = self.provider_router.get()
translated_text = provider.translate(text, "en", "fa")
```

## 2) Collaboration Service Skeleton

- Paths
  - backend/app/api/endpoints/collab.py
  - backend/app/services/collab/room_manager.py
  - backend/app/services/collab/models.py
  - backend/app/services/collab/snapshot_store.py

- WS Endpoint (FastAPI sketch)
```python
# backend/app/api/endpoints/collab.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.services.collab.room_manager import Rooms

router = APIRouter(prefix="/collab", tags=["collab"])
rooms = Rooms()

@router.websocket("/{page_id}")
async def collab_ws(websocket: WebSocket, page_id: int):
    await rooms.connect(page_id, websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            await rooms.broadcast(page_id, msg)
    except WebSocketDisconnect:
        await rooms.disconnect(page_id, websocket)
```

- Room Manager (sketch)
```python
# backend/app/services/collab/room_manager.py
from typing import Dict, Set
from fastapi import WebSocket

class Rooms:
    def __init__(self):
        self.rooms: Dict[int, Set[WebSocket]] = {}

    async def connect(self, page_id: int, ws: WebSocket):
        await ws.accept()
        self.rooms.setdefault(page_id, set()).add(ws)

    async def disconnect(self, page_id: int, ws: WebSocket):
        if page_id in self.rooms and ws in self.rooms[page_id]:
            self.rooms[page_id].remove(ws)

    async def broadcast(self, page_id: int, text: str):
        for ws in list(self.rooms.get(page_id, [])):
            try:
                await ws.send_text(text)
            except Exception:
                await self.disconnect(page_id, ws)
```

- Message Envelope (JSON)
```json
{
  "t": "presence|op|comment|suggestion|status",
  "pageId": 123,
  "user": {"id": "u_1", "name": "Alice", "role": "editor"},
  "payload": {"cursor": {"x": 0.5, "y": 0.2}}
}
```

- Snapshot Store (outline)
```python
# backend/app/services/collab/snapshot_store.py
class SnapshotStore:
    def write(self, page_id: int, data: bytes) -> str: ...
    def read(self, page_id: int) -> bytes: ...
```

- Wiring into FastAPI
```python
# backend/app/api/__init__.py (ensure router include)
# from .endpoints import collab
# app.include_router(collab.router)
```

## 3) API Contracts (Lazy Translation & Suggestions)

- POST `/documents/{id}/pages/{n}/translate`
  - Resp: `{ jobId, status }`
- GET `/documents/{id}/pages/{n}`
  - Resp: `{ pageNumber, status, source, translated, provider, cost }`
- GET `/documents/{id}/pages/{n}/suggestions`
  - Resp: `{ suggestions: [ { id, kind, diff, confidence } ] }`
- POST `/suggestions/{id}/accept` → 200 with updated segment

## 4) Environment Flags
- `TRANSLATION_PROVIDER=openai|argos|compatible|deep_translator`
- `COLLAB_ENABLED=true`

## 5) Testing Seeds
- Provider router unit test with fake providers.
- WS echo test for collab endpoint.

