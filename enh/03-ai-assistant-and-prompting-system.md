# AI Assistant, Prompting, and Instruction System

This document defines a full‑featured AI assistant for translation, editing, and research tasks within the PDF translation platform. It covers prompting patterns, instruction hierarchies, context assembly, tool use, review loops, safety, and observability.

## Objectives
- Provide expert assistance for translation, rewriting, terminology consistency, and tone control.
- Enable structured prompting and reusable instructions per user/team/document.
- Integrate retrieval (glossary, project memory, examples, research snippets) into assistant answers.
- Offer inline, contextual actions with minimal friction and clear provenance.

## Assistant Modes
- Translate: faithful translation with domain‑specific lexicon.
- Revise: rewrite with tone options (academic, concise, explanatory) while preserving meaning.
- Explain: unpack concepts, provide references, and quick summaries.
- Compare: diff alternative translations and justify a choice.
- Enforce: apply glossary and style guide; flag violations.

## Instruction Hierarchy
- System Instructions (org/tenant): legal/compliance constraints, safety rules.
- Project Instructions (document set): domain style, preferred sources, forbidden terms.
- Document Instructions (single doc): author intent, tone, audience.
- User Prompt: immediate request.
- In‑Context Examples: few‑shot segments and accepted edits.

## Context Assembly
- Base: source/target language, page/segment, neighboring segments for coherence.
- Glossary: term→translation pairs, priority, examples.
- Memory: previously accepted suggestions for similar contexts.
- Layout/Structure: headers, figure captions, tables.
- Constraints: cost/time budgets, provider caps.

## Prompt Templates (Sketch)
- Translation
  - System: “Translate preserving meaning, academic tone, obey glossary. Forbidden: hallucinations, invented citations.”
  - Project: “Use Persian punctuation; retain names; avoid over‑explanation.”
  - User: “Translate segment S” + examples.
- Revision
  - System: “Rewrite for clarity; retain meaning; mark unclear parts.”
  - User: “Revise this for concision, keep technical terms.”
- Explanation
  - System: “Explain simply; include 1–2 references if present in context.”
  - User: “What does X term mean here?”

## Tools & Functions
- Glossary Lookup: search term variants, return definitions and constraints.
- Similar Segment Retrieval: nearest neighbors by embedding.
- Cost Estimator: forecast tokens; propose budget‑respecting plan.
- Segment Actions: propose edit, create suggestion, add comment, add glossary term.
- Web Research (optional): constrained retrieval with citations.

## Providers & Routing
- Online: OpenAI‑compatible, high quality; use for hard tasks.
- Offline: Argos + finetuned components; fast/local for routine checks.
- Router selects provider by policy: quality vs cost vs latency, per request.

## Feedback & Learning
- User feedback chips (Accurate/Awkward/Missing) tune per‑project weights.
- Accepted edits become future examples; rejected advice de‑prioritized.
- Term overrides update glossary and re‑index memory store.

## Safety & Reliability
- Refuse beyond scope tasks; avoid invented sources.
- Cite only context‑available references; show source anchors.
- Redaction: strip PII in shared contexts by policy.
- Rate limits: per user and per document; backoff strategies.

## UI Entry Points
- Segment hover: “Ask Assistant,” “Improve,” “Explain,” “Enforce glossary.”
- Command palette: global actions and shortcuts.
- Sidebar chat: thread tied to page or document scope.

## Assistant Responses
- Compact by default with expand blocks; show source of truth.
- One‑click actions: “Apply suggestion,” “Create comment,” “Add term.”
- Rationale and confidence indicators with provider badge.

## Evaluation & Benchmarks
- Human eval forms: fluency, adequacy, terminology adherence.
- Automated checks: glossary enforcement score, consistency score, diff churn.
- A/B tests: provider selection, template variants, temperature settings.

## Observability
- Log structured prompts (redacted), model, latency, token usage, outcome.
- Traces across context assembly → provider call → post‑processing → UI action.

## Extensibility
- Plugins: custom tools available to assistant with restricted scopes.
- Tenant‑level instruction packs and style guides.
- Per‑team prompt libraries with sharing and versioning.

## Roadmap
- Phase 1: prompting templates + glossary tool + UI entry points.
- Phase 2: retrieval memory + suggestion auto‑apply flows.
- Phase 3: provider routing + research tool + evaluation dashboard.

