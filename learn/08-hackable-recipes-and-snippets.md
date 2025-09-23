# Hackable Recipes and Snippets

Copy-ready snippets to get things done quickly in this repo.

## Backend
- Quick translate utility
```python
from app.services.translation_service import TranslationService
print(TranslationService().translate_text("Hello world"))
```

- Add provider router usage
```python
from app.services.provider_router import ProviderRouter
router = ProviderRouter()
print(router.get().translate("text", "en", "fa"))
```

- Simple page translate endpoint
```python
@router.post('/documents/{doc_id}/pages/{n}/translate')
def translate_page(doc_id:int, n:int, db: Session = Depends(get_db)):
    from app.services.translation_service import TranslationService
    # lookup page id by doc_id + page number
    page = db.query(PDFPage).filter(PDFPage.document_id==doc_id, PDFPage.page_number==n).first()
    return TranslationService().translate_page(db, page.id)
```

## Frontend
- Lazy translate current page
```ts
const m = useMutation({
  mutationFn: async ()=> (await fetch(`/api/documents/${docId}/pages/${page}/translate`, {method:'POST'})).json(),
  onSuccess: ()=> qc.invalidateQueries({ queryKey:['page',docId,page] })
})
```

- MiniMap basic
```tsx
export default function MiniMap({pages,current,onJump}:{pages:{n:number,status:string}[],current:number,onJump:(n:number)=>void}){
  return <div className="w-60 border-r overflow-auto">
    {pages.map(p=> <button key={p.n} className={`block w-full text-left px-2 py-1 ${p.n===current?'bg-blue-100':''}`} onClick={()=>onJump(p.n)}>{p.n}</button>)}
  </div>
}
```

- Suggestion popover trigger
```tsx
<span onContextMenu={(e)=>{ e.preventDefault(); openPopoverFor(seg.id)}}>{seg.text}</span>
```

## n8n
- Provider fallback workflow skeleton: see `sub8/03-supabase-n8n-integration-recipes.md`

## Supabase
- Subscribe to page changes: see `learn/05-supabase-n8n-mastery.md`

