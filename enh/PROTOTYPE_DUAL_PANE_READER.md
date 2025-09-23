# Prototype Plan: Dual‑Pane Reader with Lazy Translation and Suggestion Popovers

This document provides a concrete, code‑ready blueprint for implementing a dual‑pane reader with lazy per‑page translation and suggestion popovers. It includes file paths, component APIs, hooks, and event flows tailored for both humans and AI coding tools.

## Route & Structure (Next.js App Router)
- frontend/app/doc/[id]/page.tsx
  - Server component fetching doc metadata; renders `ReaderPage` client component.
- frontend/app/doc/[id]/layout.tsx
  - Shell with header (title, progress, provider badge) and slots.

## Components
- frontend/components/viewer/PdfCanvas.tsx
  - Renders original PDF page via pdf.js.
  - Props: `{ fileUrl: string, pageNumber: number, zoom: number, onPageRender?: (page: number) => void }`.
- frontend/components/viewer/TranslatePane.tsx
  - Displays translated segments with anchors and suggestion decorations.
  - Props: `{ pageId: number, segments: Segment[], status: Status, onSuggest: (segId, text) => void }`.
- frontend/components/viewer/MiniMap.tsx
  - Page thumbnails + status dots; jump navigation.
  - Props: `{ pages: PageMeta[], current: number, onJump: (n:number)=>void }`.
- frontend/components/viewer/Toolbar.tsx
  - Zoom, split ratio, theme toggle, translate actions.
  - Props: `{ onTranslatePage: () => void, onSplitChange: (v:number)=>void }`.
- frontend/components/suggestions/SuggestionPopover.tsx
  - Context menu + popover showing suggestions with apply/cancel.
  - Props: `{ segment: Segment, suggestions: Suggestion[], onAccept: (id)=>void, onReject:(id)=>void }`.

## Hooks
- frontend/hooks/useTranslatePage.ts
```ts
import { useMutation, useQueryClient } from '@tanstack/react-query'
export function useTranslatePage(docId: number, pageNumber: number){
  const qc = useQueryClient()
  const m = useMutation({
    mutationFn: async () => {
      const r = await fetch(`/api/documents/${docId}/pages/${pageNumber}/translate`, { method: 'POST' })
      return r.json()
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['page', docId, pageNumber] })
  })
  return m
}
```

- frontend/hooks/usePageData.ts
```ts
import { useQuery } from '@tanstack/react-query'
export function usePageData(docId: number, pageNumber: number){
  return useQuery({
    queryKey: ['page', docId, pageNumber],
    queryFn: async () => {
      const r = await fetch(`/api/documents/${docId}/pages/${pageNumber}`)
      return r.json()
    },
    refetchInterval: (data) => (data?.status === 'processing' ? 1000 : false)
  })
}
```

- frontend/hooks/useSuggestions.ts
```ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
export function useSuggestions(docId: number, pageNumber: number){
  const qc = useQueryClient()
  const list = useQuery({
    queryKey: ['suggestions', docId, pageNumber],
    queryFn: async () => (await fetch(`/api/documents/${docId}/pages/${pageNumber}/suggestions`)).json()
  })
  const accept = useMutation({
    mutationFn: async (id: string) => (await fetch(`/api/suggestions/${id}/accept`, { method:'POST' })).json(),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['page', docId, pageNumber] })
      qc.invalidateQueries({ queryKey: ['suggestions', docId, pageNumber] })
    }
  })
  return { list, accept }
}
```

## Client Page Wire‑up
- frontend/components/ReaderPage.tsx
```tsx
'use client'
import { useState } from 'react'
import PdfCanvas from '@/components/viewer/PdfCanvas'
import TranslatePane from '@/components/viewer/TranslatePane'
import MiniMap from '@/components/viewer/MiniMap'
import Toolbar from '@/components/viewer/Toolbar'
import { usePageData } from '@/hooks/usePageData'
import { useTranslatePage } from '@/hooks/useTranslatePage'

export default function ReaderPage({ docId, fileUrl, totalPages }: { docId:number; fileUrl:string; totalPages:number }){
  const [page, setPage] = useState(1)
  const [zoom, setZoom] = useState(1)
  const { data } = usePageData(docId, page)
  const translate = useTranslatePage(docId, page)

  return (
    <div className="grid grid-cols-[240px_1fr] h-full">
      <MiniMap pages={Array.from({length: totalPages}).map((_,i)=>({n:i+1,status:'pending'}))} current={page} onJump={setPage} />
      <div className="flex flex-col h-full">
        <Toolbar onTranslatePage={() => translate.mutate()} onSplitChange={()=>{}} />
        <div className="grid grid-cols-2 gap-2 h-full">
          <PdfCanvas fileUrl={fileUrl} pageNumber={page} zoom={zoom} />
          <TranslatePane pageId={data?.pageId} segments={data?.segments||[]} status={data?.status} onSuggest={()=>{}} />
        </div>
      </div>
    </div>
  )
}
```

## Suggestion Popover Interaction
- Trigger: right‑click on a segment or select text in TranslatePane.
- Flow
  - Open popover with candidate suggestions (from API or local heuristic).
  - Apply writes via `POST /suggestions/{id}/accept`; UI updates optimistically.
  - Recompute quality/scores in background.

## Events and Telemetry
- viewer.page_view, translate.request, translate.first_token, translate.complete.
- suggestion.open, suggestion.accept, suggestion.reject.

## Styling & Motion
- Use Radix UI popover + shadcn/ui primitives; Tailwind for layout.
- Micro‑animations via Framer Motion: popover fade/scale 120ms; segment accept 250ms.

## Accessibility
- Keyboard: open popover via menu key; navigate suggestions with arrows; Enter to accept.
- ARIA roles for menu/listbox; focus trap inside popover; restore focus to segment.

## API Requirements
- Ensure backend routes from SCAFFOLD_COLLAB_AND_PROVIDERS.md are present.
- Add CORS allowances for WS and REST paths if needed.

## Acceptance Criteria (Prototype)
- Navigate pages; request lazy translate; see status update without reload.
- Open suggestion popover on a segment and simulate accept via mocked API.
- No layout shift during translations; reduced motion respected.

