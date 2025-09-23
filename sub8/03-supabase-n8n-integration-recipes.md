# Integration Recipes: Supabase + n8n With Our Backend/Frontend

This document provides practical recipes to combine Supabase (auth, realtime, storage) with n8n (automation) and our FastAPI/Next.js apps. Designed to be copy‑pastable by humans and AI tools.

## 1) Realtime Page Status via Supabase
- Goal: Replace polling with realtime updates for page status.
- Steps
  1. Emit a DB update to `pages.status` on backend commit.
  2. Subscribe in Next.js to `realtime:public:pages:document_id=eq.{docId}`.
- Client snippet (TS)
```ts
import { createClient } from '@supabase/supabase-js'
const supabase = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!)
export function subscribePageStatus(docId: number, cb: (p:any)=>void){
  return supabase.channel(`pages-${docId}`)
    .on('postgres_changes', { event: '*', schema: 'public', table: 'pages', filter: `document_id=eq.${docId}` }, (payload)=>cb(payload.new))
    .subscribe()
}
```

## 2) Presence Channels for Collaboration
- Goal: Lightweight presence via Supabase before full CRDT.
- Steps
  - Use Realtime Presence API: `presence:page-{pageId}` channel.
- Client snippet
```ts
const channel = supabase.channel(`presence:page-${pageId}`, { config: { presence: { key: userId } } })
channel.on('presence', { event: 'sync' }, () => {
  const state = channel.presenceState()
  // render avatars/cursors
}).subscribe(async (status) => {
  if (status === 'SUBSCRIBED') await channel.track({ cursor: { x: 0.2, y: 0.3 } })
})
```

## 3) Webhook Security for n8n
- Goal: Verify HMAC signatures for `/hooks/n8n/*`.
- FastAPI sketch (Py)
```python
from fastapi import APIRouter, Request, HTTPException
import hmac, hashlib, os
router = APIRouter(prefix='/hooks/n8n', tags=['n8n'])

SECRET = os.environ.get('N8N_HOOK_SECRET','change-me')

def verify(req_body: bytes, signature: str):
    mac = hmac.new(SECRET.encode(), msg=req_body, digestmod=hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, signature)

@router.post('/page-status')
async def page_status(request: Request):
    raw = await request.body()
    sig = request.headers.get('x-signature','')
    if not verify(raw, sig):
        raise HTTPException(status_code=401, detail='invalid signature')
    payload = await request.json()
    # enqueue processing, maybe fallback provider
    return { 'ok': True }
```

## 4) Storage Uploads via Supabase
- Goal: Use Supabase buckets for uploads and previews.
- Client flow
  - Next.js requests signed URL from API; client PUTs file; API stores metadata.
- API sketch (Py)
```python
# sign upload URL
@router.post('/uploads/sign')
async def sign_upload(file_name: str):
    # use supabase python client or jwt to sign
    return { 'url': 'https://supabase/...signed...' }
```

## 5) n8n Provider Fallback Workflow JSON (Skeleton)
```json
{
  "nodes": [
    { "id": "webhook1", "type": "n8n-nodes-base.webhook", "parameters": { "path": "page-status", "httpMethod": "POST" } },
    { "id": "ifFailed", "type": "n8n-nodes-base.if", "parameters": { "conditions": { "string": [{ "value1": "={{$json.status}}", "operation": "equal", "value2": "failed" }] } } },
    { "id": "retryArgos", "type": "n8n-nodes-base.httpRequest", "parameters": { "url": "https://api.local/api/documents/{{$json.docId}}/pages/{{$json.pageNumber}}/translate", "method": "POST", "jsonParameters": true, "options": {}, "sendBody": true, "bodyParametersJson": "{\"provider\":\"argos\"}" } },
    { "id": "slackNotify", "type": "n8n-nodes-base.slack", "parameters": { "operation": "postMessage", "channel": "#alerts", "text": "Fallback triggered for doc {{$json.docId}} page {{$json.pageNumber}}" } }
  ],
  "connections": { "webhook1": { "main": [[{ "node": "ifFailed", "type": "main", "index": 0 }]] }, "ifFailed": { "main": [[{ "node": "retryArgos", "type": "main", "index": 0 }, { "node": "slackNotify", "type": "main", "index": 0 }]] } }
}
```

## 6) Supabase Edge Function to Kick Backend Job
- Deno function snippet
```ts
// supabase/functions/on-upload/index.ts
import { serve } from "https://deno.land/std/http/server.ts"
serve(async (req) => {
  const body = await req.json()
  // call backend to start parse job
  await fetch(`${Deno.env.get('API_BASE')}/api/documents/${body.docId}/parse`, { method: 'POST' })
  return new Response(JSON.stringify({ ok: true }), { headers: { 'content-type': 'application/json' } })
})
```

## 7) End‑to‑End Flow Example
- User uploads PDF → Supabase Storage → Edge Function → Backend parse/OCR → Supabase `pages` rows inserted → Realtime notifies Next.js → User clicks translate → Backend calls provider → status updates stream back via Realtime → n8n receives webhooks for analytics/alerts.

## Risks & Notes
- Keep secrets out of clients; use service role on server only.
- Backpressure: batch updates to `pages` to reduce realtime noise.
- Version workflow JSON and Edge Functions alongside code changes.

