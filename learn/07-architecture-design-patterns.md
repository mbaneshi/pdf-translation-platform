# Architecture and Design Patterns

Understand the system holistically and build change-friendly features.

## Principles
- Separation of concerns: endpoints thin; services own business logic
- Dependency injection: pass DB/config; pure functions where feasible
- Feature flags: ship incrementally; support dark launches
- Idempotency: safe retries for jobs and endpoints

## Module Boundaries
- API (transport) vs Services (domain) vs Data access (repositories)
- Providers as adapters implementing a stable interface

## Patterns
- Strategy: provider selection via router
- Observer: realtime events to UI and n8n
- Command: accept/reject suggestion actions
- Saga (process manager): long-running translation flows with retries

## Anti-Patterns
- Business logic in controllers; tight coupling to a single provider
- Hidden global states; missing error handling for provider limits

## Documentation
- Keep specs in `enh/` and `learn/` up-to-date with implemented behavior

