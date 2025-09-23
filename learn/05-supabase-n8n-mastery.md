# Supabase and n8n Mastery

Layer Supabase (auth/RLS/realtime/storage) and n8n (workflow automation) onto our stack.

## Supabase
- Use as primary or sidecar for collaboration/realtime and storage
- RLS policies to enforce tenant/document access
- Realtime channels for `pages`, `comments`, `suggestions`

### Client Realtime Snippet
```ts
import { createClient } from '@supabase/supabase-js'
const supabase = createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!)
export function subscribePageStatus(docId: number, cb: (p:any)=>void){
  return supabase.channel(`pages-${docId}`)
    .on('postgres_changes', { event: '*', schema: 'public', table: 'pages', filter: `document_id=eq.${docId}` }, (payload)=>cb(payload.new))
    .subscribe()
}
```

## n8n
- Automate fallback provider retries, nightly glossary enforcement, QA sampling, analytics sync
- Secure webhooks with HMAC; store workflow JSON under `ops/n8n/`

### Webhook HMAC (FastAPI)
```python
mac = hmac.new(SECRET.encode(), msg=raw_body, digestmod=hashlib.sha256).hexdigest()
```

## End-to-End
- Upload → parse → realtime updates → translate → webhook to n8n → fallback/notify → suggestions → review

## Next
- See `sub8/01-supabase-strategy.md` and `sub8/02-n8n-strategy.md` for details

