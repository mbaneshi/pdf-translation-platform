# Suggestions, Glossary, and Quality Feedback System

This document specifies the end‑to‑end system for suggestions, glossary enforcement, and quality feedback loops to elevate translation quality and team workflows.

## Objectives
- Make high‑quality suggestions easy to generate, review, and accept at scale.
- Enforce terminology consistently with rich, context‑aware glossaries.
- Turn user feedback into measurable improvements and project memory.

## Suggestions Lifecycle
- Create
  - Sources: AI assistant, reviewer edits, glossary rule triggers.
  - Scope: word/phrase/segment; batch per page or across matched terms.
- Review
  - Diff view: word‑level highlighting; show glossary impacts.
  - Actions: accept, reject, modify into new suggestion.
- Apply
  - Updates segment; writes version; closes suggestion.
- Learn
  - Accepted → added to memory/examples; rejected → de‑prioritize patterns.

## Glossary Model
- Term: base form, variants, language, part of speech.
- Translation: preferred, alternates, forbidden.
- Context: domain tags, examples, notes, priorities.
- Policies: enforce strict/lenient, case handling, inflection rules.

## Enforcement Engine
- Detection: FSTs/regex for variants; embedding similarity for tricky cases.
- Scoring: severity (critical, major, minor); surface as badges.
- Actions: auto‑suggest replacements; batch fix with review.
- Exceptions: per‑segment override with explanation.

## Quality Signals
- Adequacy, Fluency, Consistency, Terminology, Formatting.
- Compute heuristics + model‑assisted checks; roll up to page/document score.
- Show deltas after suggestions and reviewer passes.

## Reviewer Tools
- Multi‑select suggestions; accept in bulk with rationale.
- Assign suggestions to teammates; due dates; notifications.
- Saved filters: by severity, page range, assignee, term.

## UI Patterns
- SuggestionCard: compact summary with expand for full diff and context.
- GlossaryBadge: hover for definition and examples.
- QualityMeter: per page with drill‑down panel.

## Batch Operations
- “Fix glossary violations on this page” → previews changes → single confirm.
- “Accept AI rephrase for clarity” with confidence ≥ threshold.

## Metrics
- Suggestion acceptance rate by source and severity.
- Glossary coverage and violation trend over time.
- Review throughput: time to accept/reject, backlog aging.

## Data Schema
- suggestions(id, segment_id, source, diff, created_by, confidence, status)
- glossary_terms(id, term, lang, pos, rules, examples, priority)
- glossary_translations(id, term_id, target_lang, preferred, alternates, forbidden)
- quality_scores(id, level, page_id?, doc_id?, metrics_json, ts)

## API Endpoints
- POST /glossary/terms, PATCH /glossary/terms/:id
- GET /documents/:id/pages/:n/suggestions
- POST /suggestions/:id/accept, POST /suggestions/:id/reject
- POST /quality/score/recompute

## Automation Policies
- Run enforcement after translation finishes; or on demand.
- Nightly recompute of quality scores; notify regressions.
- Auto‑close suggestions stale > 90 days (configurable).

## Integrations
- Export suggestions in CSV/JSON for batch review offline.
- Import finalized edits back; reconcile by segment anchors.

## Risks
- Over‑enforcement noise → tune thresholds; user suppression rules.
- Diff ambiguity on complex text → fallback to sentence diff.

