# Frontend Mastery: Next.js, App Router, and Reader UX

Learn how our Next.js app is structured and how to build the dual‑pane reader and suggestion UI.

## Structure
- App: `frontend/app/` (migrate from `pages/` gradually)
- Components: `frontend/components/`
- Hooks: `frontend/hooks/`
- Config: `frontend/tsconfig.json`, `jest.config.ts`, `tailwind.config.js`

## Dev
- `cd frontend && npm install && npm run dev`
- Tests: `npm test`

## Key Concepts
- Server Components by default; client components for interactive pieces
- TanStack Query for server state; Zustand for UI state
- Tailwind + Radix + shadcn/ui for accessible components

## Reader Skeleton (files to create)
- `frontend/app/doc/[id]/page.tsx`: fetch doc meta, render ReaderPage
- `frontend/components/viewer/PdfCanvas.tsx`: pdf.js canvas rendering
- `frontend/components/viewer/TranslatePane.tsx`: translated segments
- `frontend/components/viewer/MiniMap.tsx`: thumbnails + status dots
- `frontend/components/viewer/Toolbar.tsx`: translate/zoom/theme controls

## Hooks (sketch)
```ts
// usePageData.ts
import { useQuery } from '@tanstack/react-query'
export function usePageData(docId:number, pageNumber:number){
  return useQuery({
    queryKey:['page',docId,pageNumber],
    queryFn: async ()=> (await fetch(`/api/documents/${docId}/pages/${pageNumber}`)).json(),
    refetchInterval: (data)=> data?.status==='processing'? 1000:false
  })
}
```

## Testing Patterns
- RTL + Jest for components; Playwright for reader flows
- Example
```ts
import { render, screen } from '@testing-library/react'
import MiniMap from '@/components/viewer/MiniMap'
test('shows current page', ()=>{
  render(<MiniMap pages={[{n:1,status:'done'}]} current={1} onJump={()=>{}} />)
  expect(screen.getByText('1')).toBeInTheDocument()
})
```

## A11y & Perf
- Keyboard shortcuts (J/K next/prev page, T translate)
- Respect `prefers-reduced-motion`; avoid layout shift
- Code-split pdf.js worker; virtualize long lists

## Next
- Follow `enh/PROTOTYPE_DUAL_PANE_READER.md` to build the prototype

