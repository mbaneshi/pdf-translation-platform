# Translation Platform Enhancements – Version 2

This iteration adds: (1) concrete UI upgrades, (2) an agentic design using CrewAI (or similar), and (3) a quick 20‑page trial procedure to benchmark output and UX.

## 1) UI Enhancements (Next.js)

Goals: visibility, control, quality review, and export.

- Document List + Filters
  - Columns: filename, pages, status (uploaded/extracted/translating/completed), progress %, created_at.
  - Actions: open, delete, resume job.
- Document Detail Dashboard
  - Header: cost to date, token usage, elapsed time, model.
  - Progress bar: pages done / total; ETA.
  - Tabs:
    - Pages: table with page_number, status, tokens, cost, duration; actions: sample translate, open chunk view.
    - Glossary: CRUD (term/source, target, notes), import/export CSV.
    - Review: list of flagged chunks (low quality score, glossary violations) with inline editor and accept/reject.
    - Exports: buttons for Markdown/HTML/DOCX; include tables/lists.
  - Right panel: live job log (stream), Flower link, retry controls.
- Page View
  - Side‑by‑side original vs translated (RTL support), toggle diff view.
  - Chunk viewer: show chunk boundaries, types (paragraph/list/table), and model usage.
  - Table preview: render markdown tables nicely.
- Global UX + i18n
  - Robust RTL styling for Persian (font, punctuation, line spacing). Tailwind utilities for [dir=rtl].
  - Toasts for long‑running actions; cancel tokens for polling.

API hooks (frontend)
- `useDocument(id)`, `usePages(documentId)`, `useTranslateSample(documentId, page)`, `useJobStatus(documentId)`.
- Web‑safe polling: exponential backoff; stop on terminal states.

Minimal scope to ship first
- Document list/detail + pages table + sample translate button + progress polling.
- Side‑by‑side page preview + export to Markdown.

## 2) Agentic Design (CrewAI or LangGraph)

Intent: encapsulate pipeline steps into cooperating agents, while reusing our Celery workers for execution at scale.

Agent roster
- OrchestratorAgent
  - Plans job, selects chunk strategy, coordinates agents.
  - Inputs: document meta, user options (model, chunk_size, glossary).
  - Outputs: work plan and chunk map.
- IngestionAgent
  - Validates PDF, extracts text + layout (uses existing PDFService).
  - Output: page structures and layout metadata.
- ChunkerAgent
  - Produces token‑aware, layout‑aware chunks, deduplicates headers/footers.
  - Output: chunks[] with type, offsets, token counts, hash.
- TerminologyAgent
  - Builds/extends glossary from domain cues; flags term conflicts.
  - Output: glossary set and constraints for prompts.
- TranslationAgent
  - Translates chunks deterministically with structure‑aware prompts; caches by hash.
  - Output: translated chunks + usage (tokens), intermediate cost.
- ReviewAgent
  - Performs LLM QA pass; suggests minimal edits; checks glossary adherence and Persian conventions.
  - Output: edited text + quality metrics per chunk.
- RateGuardAgent
  - Enforces global rate limits (Redis token bucket), handles 429 backoff policy.

Execution model
- Light‑weight agent layer for planning/decisions; Celery continues to do chunk translation tasks for throughput.
- Agents expose “tools” that submit Celery tasks and await results; persistent state in DB (page metadata) or Redis.

Data contracts (sketch)
- Chunk: `{id, page_id, type, text, tokens, hash, order, layoutHints}`
- TranslationResult: `{chunk_id, text, usage: {in,out}, model, cost}`
- ReviewResult: `{chunk_id, editedText, score, issues[]}`

Benefits
- Clear separation of concerns; easier to test and swap components.
- Add/focus agents incrementally without breaking current pipeline.

Risks + mitigations
- Complexity: start with Orchestrator + Chunker + Translation; add Review later.
- Ops: keep Celery as the execution backbone; agents remain stateless planners.

## 3) Quick Trial: 20‑Page Benchmark

Purpose: compare quality and UX quickly using the running stack. We’ll translate the first 20 pages and compare with your alternate pipeline in `trnslation/`.

Prereqs
- Stack is up (Traefik routing OK). You have a PDF at repo root (e.g., `Bruce_*.pdf`) or use `test.pdf`.
- Tools: curl, jq.

Steps
1) Upload the PDF via enhanced endpoint (layout preserved):

```
DOC=$(curl -s -F file=@"Bruce_Hyde,_Drew_Kopp_Speaking_Being_Werner_Erhard,_Martin_Heidegger\ \(1\).pdf" \
  https://apipdf.edcopo.info/api/enhanced/upload-enhanced | jq -r '.document_id')
echo "document_id=$DOC"
```

2) Inspect pages list (optional):
```
curl -s https://apipdf.edcopo.info/api/documents/$DOC/pages | jq '.[0:5]'
```

3) Translate first 20 pages using the sample endpoint (synchronous per page). This marks pages as test and returns text; saves outputs for review.

```
mkdir -p trial && : > trial/pdftr_20pages.txt
for i in $(seq 1 20); do
  echo "\n===== PAGE $i =====\n" | tee -a trial/pdftr_20pages.txt
  curl -s -X POST \
    https://apipdf.edcopo.info/api/enhanced/translate-sample/$DOC/page/$i \
    | jq -r '.translated_text' | tee -a trial/pdftr_20pages.txt
  sleep 0.5
done
```

4) Produce a baseline from your other pipeline in `~/pdf/trnslation` (adjust if needed):

- If it already generated `translated.txt`, copy:
```
cp ~/pdf/trnslation/translated.txt trial/baseline_20pages.txt || true
```
- Or run your script (example):
```
cd ~/pdf/trnslation
python ingest.py sample.pdf > exported_translations.txt
cp exported_translations.txt ~/pdf/pdf-translation-platform/trial/baseline_20pages.txt
```

5) Quick comparisons:

- Character/word counts and Persian presence:
```
python - << 'PY'
import os, re
p = re.compile(r'[\u0600-\u06FF]')
A = open('trial/pdftr_20pages.txt','r').read()
B = open('trial/baseline_20pages.txt','r').read() if os.path.exists('trial/baseline_20pages.txt') else ''
print('pdftr length:', len(A), 'persian:', bool(p.search(A)))
print('base length:', len(B), 'persian:', bool(p.search(B)))
PY
```

- Simple diff (human scan):
```
wdiff -n trial/baseline_20pages.txt trial/pdftr_20pages.txt | sed -n '1,120p' || diff -u trial/baseline_20pages.txt trial/pdftr_20pages.txt | sed -n '1,120p'
```

6) Optional: Kick off full background translation for the document and watch progress:
```
curl -s -X POST https://apipdf.edcopo.info/api/enhanced/gradual-translate/$DOC | jq
watch -n 5 "curl -s https://apipdf.edcopo.info/api/enhanced/translation-progress/$DOC | jq"
```

Notes
- The sample endpoint is a synchronous path for quick trials; the background job is the scalable path.
- Page output is raw text; V2 plan includes structure‑aware markdown + export.
- If you hit rate limits, add small sleeps or run in smaller batches.

## What I Can Do Next

- Start Phase 1 implementation (chat API client + token‑aware chunking + usage/cost tracking) behind a feature flag.
- Scaffold minimal frontend: document detail + pages + sample translate + progress polling.
- Optional: introduce a minimal Orchestrator + Chunker agent (CrewAI) that delegates to existing services.

Share preferences on model choice, UI priorities, and whether to pilot the agent layer in a feature branch.
