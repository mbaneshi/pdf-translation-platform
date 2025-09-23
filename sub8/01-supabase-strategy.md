# Supabase Strategy: How Self‑Hosted Supabase Accelerates Our Platform

This document outlines how a self‑hosted Supabase stack (Postgres + Realtime + Auth + Storage + Edge Functions) can accelerate our roadmap for a collaborative, AI‑assisted PDF translation platform. It is optimized for humans and AI coding tools with concrete paths, schemas, and policies.

## Why Supabase (Self‑Hosted)
- Managed Postgres with batteries included: Auth, Storage, Realtime, Row‑Level Security (RLS), Edge Functions.
- Realtime channels over websockets built on logical replication (supabase/realtime) — excellent fit for presence, status updates, and comments.
- Self‑hosting preserves data sovereignty and compliance needs.

## High‑Value Capabilities For Us
- Auth & RBAC
  - Email/password, OAuth, SSO via SAML/OIDC. JWTs easy to verify in FastAPI + Next.js.
  - Row‑Level Security to enforce per‑tenant, per‑document, per‑page permissions.
- Realtime
  - Push page status changes, presence, and comments without building infra from scratch.
- Storage
  - Store PDFs, previews, exports with signed URLs and object versioning.
- Edge Functions
  - Lightweight webhooks, pre‑processing, or routing to our API with low latency.

## Where Supabase Fits
- Source of Truth for Collaboration metadata (comments/threads, presence heartbeats, assignments, suggestions index). Postgres remains our primary DB or replicates from our DB.
- Realtime layer for: presence, page translation status, suggestion updates.
- Storage for artifacts: uploaded PDFs, thumbnails, exported PDFs, JSONL audits.
- Auth provider issuing JWTs for API and WebSocket authorization.

## Integration Topologies
- Option A: Supabase as primary DB
  - Migrate current SQLAlchemy models to Supabase Postgres.
  - Use RLS for multi‑tenant security; use Supabase Realtime for live updates.
- Option B: Supabase as collaboration sidecar
  - Keep our DB as the system of record for documents/pages.
  - Mirror collaboration tables (comments/suggestions/presence) to Supabase.
  - Use Edge Functions for triggers/webhooks to sync back to our API.

## Proposed Tables (DDL Sketch)
```sql
-- Tenancy & Access
create table tenants (
  id uuid primary key default gen_random_uuid(),
  name text not null
);

create table memberships (
  user_id uuid not null,
  tenant_id uuid not null references tenants(id),
  role text not null check (role in ('owner','admin','editor','reviewer','viewer')),
  primary key (user_id, tenant_id)
);

-- Documents & Pages (mirrors of our backend, if primary in Supabase)
create table documents (
  id bigserial primary key,
  tenant_id uuid not null references tenants(id),
  title text,
  file_url text,
  total_pages int,
  created_by uuid,
  created_at timestamptz default now()
);

create table pages (
  id bigserial primary key,
  document_id bigint not null references documents(id) on delete cascade,
  page_number int not null,
  status text not null default 'pending',
  provider text,
  cost_estimate numeric,
  translated_at timestamptz
);

-- Collaboration & Review
create table comments (
  id bigserial primary key,
  page_id bigint not null references pages(id) on delete cascade,
  segment_anchor jsonb not null,
  author_id uuid not null,
  body text not null,
  status text not null default 'open',
  created_at timestamptz default now()
);

create table suggestions (
  id bigserial primary key,
  page_id bigint not null references pages(id) on delete cascade,
  segment_anchor jsonb not null,
  source text not null,
  diff jsonb not null,
  confidence numeric,
  status text not null default 'open',
  created_by uuid,
  created_at timestamptz default now()
);

-- Presence (ephemeral, but can be stored)
create table presence (
  user_id uuid,
  page_id bigint,
  cursor jsonb,
  updated_at timestamptz default now(),
  primary key (user_id, page_id)
);
```

## Row‑Level Security (RLS) Policies
```sql
alter table documents enable row level security;
create policy tenant_isolation on documents
  for select using (exists (
    select 1 from memberships m
    where m.user_id = auth.uid() and m.tenant_id = documents.tenant_id
  ));

alter table pages enable row level security;
create policy page_read on pages
  for select using (exists (
    select 1 from documents d
    join memberships m on m.tenant_id = d.tenant_id
    where d.id = pages.document_id and m.user_id = auth.uid()
  ));
```

## Realtime Channels
- Pages: `realtime:public:pages:id=eq.{page_id}` for status/provider updates.
- Comments: `realtime:public:comments:page_id=eq.{page_id}` for new comments.
- Suggestions: `realtime:public:suggestions:page_id=eq.{page_id}` for updates.
- Presence: dedicated channel `presence:page-{page_id}` using Supabase Realtime Presence API.

## Auth Integration
- Next.js: `@supabase/ssr` for server components and client helpers.
- FastAPI: verify Supabase JWT with public JWK; map to internal user/tenant.
- WebSocket: token passed as query or header, validated server‑side.

## Storage Strategy
- Buckets: `uploads`, `previews`, `exports`, `audits`.
- Signed URLs with short TTL for viewer; long‑lived for exports with audit rules.

## Edge Functions (Deno) Use Cases
- On comment creation → webhook to backend to recompute quality highlights.
- On suggestion accept → write audit JSONL to `audits` bucket and ping analytics.
- On upload finalization → kick backend OCR/parse job.

## API Contracts (Frontend)
- Subscribe to realtime updates instead of polling where feasible.
- Fallback polling for compatibility, keep intervals modest.

## Migration Plan
- Phase 1: Sidecar — create collaboration tables and wire realtime for pages/comments.
- Phase 2: Auth switch — move web auth to Supabase; keep API compatible.
- Phase 3: Storage — migrate uploads/exports to Supabase buckets.
- Phase 4: Optional — move primary doc/page tables to Supabase.

## Risks & Mitigations
- RLS complexity → start with read policies, add write later; robust tests.
- Realtime volume → throttle updates; aggregate status messages server‑side.
- JWT validation drift → cache JWKs and add fallback.

## Actionable Tickets
- Provision self‑hosted Supabase with SSL and backups.
- Set up schemas + RLS; create service role for backend.
- Integrate Next.js with Supabase client; wire viewer status via realtime.
- Write Edge Function for upload finalization webhook.

