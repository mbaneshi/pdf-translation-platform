# Side‑by‑Side Reader UX & Micro‑Interactions

This document defines a modern, polished side‑by‑side reader with real‑time translation, intuitive controls, and tasteful micro‑interactions. It aims for a premium experience: fast, accessible, and delightful without gimmicks.

## Experience Pillars
- Flow: uninterrupted reading with lazy per‑page translation and background prefetch.
- Control: powerful yet simple toolbar, keyboard shortcuts, and context actions.
- Feedback: clear statuses, progress, and costs without clutter.
- Delight: restrained motion and haptics that reinforce meaning.

## Layout Anatomy
- App Shell: sticky header (title, progress, provider), collapsible left mini‑map, right review drawer.
- Dual Panes: left “Original PDF” (pdf.js canvas), right “Translated” (rich text with anchors).
- Sync Bar: locks scrolls and zoom; toggles to adjust coupling.

## Toolbar
- Zoom: fit width/page, +/- zoom with ctrl/cmd + mousewheel support.
- Split: draggable divider, snap points 30/50/70%, keyboard adjustable.
- Theme: light/dark/system, high‑contrast, reduce motion.
- Translate: page translate, section translate, translate to current.
- Export: current page, selected pages, full doc with audit.

## Mini‑Map
- Shows page thumbnails with status dots: pending, processing, done, failed.
- Hover preview with quick actions: translate, retranslate, open review.
- Search: jump to pages with certain text (indexed highlights).

## Micro‑Interactions
- Status Dot
  - Pending → Processing: subtle pulse to indicate work started.
  - Processing → Done: checkmark morph; bounce limited to 1.2 scale.
  - Failed: shake 2px left‑right twice.
- Pane Transition
  - On translation completion, fade‑in translated segments sequentially (50ms stagger).
- Tooltip Motion
  - Ease in/out with 120ms; minimal elevation shadow.
- Diff Accept
  - Merge animation: highlighted words tween to final positions; 250ms.

## Keyboard Shortcuts
- Navigation: J/K next/prev page; H/L previous/next segment; G go to page.
- Actions: T translate page; S split ratio cycle; Z zoom controls; E open review.
- Review: A accept suggestion; R reject; C comment; M toggle mini‑map.

## Accessibility
- Focus management: restore focus to last control after dialogs; focus traps.
- ARIA: landmarks for panes; status live regions for translation updates.
- Contrast and motion: WCAG AA; respect `prefers-reduced-motion`.
- Screen reader support for page/segment context and controls.

## Performance Targets
- Initial render: viewer interactive < 1s after route change on warmed cache.
- Page switch: < 200ms to display new page thumbnail and canvas.
- Translation stream: first tokens visible < 500ms after request starts.
- 60fps on scroll/zoom; virtualization for long documents.

## Rendering Strategy
- pdf.js worker for original pane; off‑main‑thread rendering.
- Translate pane uses HTML with anchors mapping to source bbox spans; maintain selection mapping.
- Virtualize pages and segments; only render the viewport + buffer.

## Real‑Time Updates
- WebSocket/SSE to push page status changes and streamed translations.
- Optimistic UI: show “processing” immediately; cancel/undo for user‑initiated actions.
- In‑place updates to segments; preserve scroll position and selection.

## Context Menus
- On segment: “Suggest edit,” “Comment,” “Copy source/target,” “Add term to glossary.”
- On selection: “Translate selection,” “Glossary lookup,” “Rewrite tone.”
- On page: “Translate page,” “Retranslate,” “Export page.”

## Error Handling
- Soft errors: inline banners with retry button; preserve content.
- Hard errors: modal with context (provider, tokens); copyable diagnostic id.
- Automatic fallback: switch provider if policy allows; notify and log.

## Cost Telemetry
- Show per‑page token estimate before translate; confirm if over threshold.
- Collapse to compact badge after acceptance; detailed breakdown in review panel.

## Internationalization & RTL
- Bidirectional support: mirrored layout for RTL target languages.
- Persian typography controls: line height, justification, ligatures.

## Design Tokens
- Color system with semantic roles (info/success/warn/danger/neutral).
- Elevation: 3 levels; consistent shadows.
- Radii and spacing scale; consistent interactive target sizes (44px min).

## Animations Catalog (Framer Motion)
- Page thumbnail hover: scale 1.02, duration 120ms.
- Divider drag: spring for release snap.
- Toasts: slide‑in from bottom‑right, overshoot 1.05.
- Suggestions list mount/unmount: vertical collapse/expand.

## Progressive Features
- PWA: offline cached assets and last N pages; background sync.
- Smart prefetch: anticipate next pages by scroll direction and speed.

## Quality Bars
- Lighthouse: Performance ≥ 90, A11y ≥ 95, Best Practices ≥ 95.
- UXR: task success (translate selected pages) ≥ 95% within 3 clicks.

## Component Inventory
- Viewer primitives: PdfCanvas, TranslatePane, SyncScrollProvider, MiniMap, Toolbar.
- Review primitives: SegmentList, SuggestionCard, DiffView, GlossaryBadge, CommentThread.
- System: UploadDropzone, Toast, Dialog, ProgressBar, ProviderBadge, CostMeter.

## State Management
- UI state via Zustand (view settings, panel open state, active selection).
- Server state via TanStack Query (page status, translation jobs), with WebSocket cache invalidation.

## Testing Plan
- Visual: Storybook for all components with a11y checks.
- E2E: Playwright for critical reader flows and keyboard navigation.
- Perf: Lighthouse CI on PR; interaction traces for scroll/zoom.

## Telemetry Events
- `viewer.page_view`, `viewer.segment_select`, `translate.request`, `translate.first_token`, `translate.complete`, `suggestion.accept`, `glossary.add_term`, `error.inline_retry`.

## Rollout Plan
- Beta: behind a feature flag per tenant; opt‑in.
- Gradual: enable for 10% of docs; monitor metrics; ramp up weekly.

## Risk Log
- High CPU usage on pdf.js → throttle thumbnail rendering; cache.
- Scroll sync complexity → use normalized scroll ratios with hysteresis.
- Over‑animation → strict motion tokens; reduced motion default on low‑end.

