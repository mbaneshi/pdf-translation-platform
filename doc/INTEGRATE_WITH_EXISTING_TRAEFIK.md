# Integrate This Stack With an Existing Traefik Proxy

This runbook shows how to run this repository (API + Web + Worker + Monitor) behind an already-running Traefik v2 proxy that uses Cloudflare DNS challenge and an external Docker network (e.g., `traefik-proxy`). It complements the migration guide in `doc/MIGRATING_FROM_CADDY_TO_TRAEFIK.md`.

Use this if you already have a central Traefik stack and want this app to plug into it without running another Traefik instance.

## Assumptions

- Your Traefik is already up, using:
  - Docker provider, file provider (for middlewares)
  - ACME via Cloudflare DNS (`certresolver: cloudflare`)
  - External Docker network: `traefik-proxy` (name may differ)
- You control DNS for the following hostnames and can point them to the Traefik host:
  - Frontend: `pdf.edcopo.info`
  - Backend API: `apipdf.edcopo.info`
  - Optional: `flower.edcopo.info` (Celery Flower)

## High-Level Steps

1) Join services to Traefik’s external network (do not publish host ports)
2) Add Traefik labels (routers, TLS, middlewares, service ports)
3) Remove the local `caddy` service
4) Update DNS records to the Traefik host
5) Deploy and verify via Traefik dashboard and curl

## 1) Add the external proxy network to compose

In `docker-compose.yml`, declare the external network used by your Traefik stack, e.g.:

```yaml
networks:
  traefik-proxy:
    external: true
  pdftr_default:
    driver: bridge
```

Keep `pdftr_default` for internal comms (db/cache ↔ app). The Traefik-facing services will join both `pdftr_default` and `traefik-proxy`.

## 2) Remove Caddy and host-published ports (Traefik terminates TLS)

- Delete the `caddy` service block.
- For `api`, `web`, and `monitor`, remove `ports: ["8000:8000"]`, `"3000:3000"`, `"5555:5555"` after initial validation. During first cutover, you may leave them temporarily to debug, then remove.

## 3) Add Traefik labels and networks to services

Attach each service to `traefik-proxy` and add labels. If your Traefik middlewares include `studio-auth@file`, `cors-wildcard@file`, or `api-rate@file`, you can attach them as shown.

Backend API (`api`, container listens on 8000):

```yaml
services:
  api:
    # ...existing config...
    networks: [pdftr_default, traefik-proxy]
    labels:
      traefik.enable: "true"
      traefik.docker.network: traefik-proxy
      traefik.http.routers.api.rule: "Host(`apipdf.edcopo.info`)"
      traefik.http.routers.api.entrypoints: "websecure"
      traefik.http.routers.api.tls: "true"
      traefik.http.routers.api.tls.certresolver: "cloudflare"
      # Middlewares (optional, adjust to your Traefik dynamic.yml)
      # traefik.http.routers.api.middlewares: "cors-wildcard@file,api-rate@file"
      traefik.http.services.api.loadbalancer.server.port: "8000"
```

Frontend (`web`, container listens on 3000):

```yaml
services:
  web:
    # ...existing config...
    networks: [pdftr_default, traefik-proxy]
    labels:
      traefik.enable: "true"
      traefik.docker.network: traefik-proxy
      traefik.http.routers.web.rule: "Host(`pdf.edcopo.info`)"
      traefik.http.routers.web.entrypoints: "websecure"
      traefik.http.routers.web.tls: "true"
      traefik.http.routers.web.tls.certresolver: "cloudflare"
      # traefik.http.routers.web.middlewares: "secure-headers@file"
      traefik.http.services.web.loadbalancer.server.port: "3000"
```

Celery Flower (`monitor`, container listens on 5555), protected with basic auth if available:

```yaml
services:
  monitor:
    # ...existing config...
    networks: [pdftr_default, traefik-proxy]
    labels:
      traefik.enable: "true"
      traefik.docker.network: traefik-proxy
      traefik.http.routers.flower.rule: "Host(`flower.edcopo.info`)"
      traefik.http.routers.flower.entrypoints: "websecure"
      traefik.http.routers.flower.tls: "true"
      traefik.http.routers.flower.tls.certresolver: "cloudflare"
      # Protect with basic auth if defined in your dynamic.yml
      # traefik.http.routers.flower.middlewares: "studio-auth@file"
      traefik.http.services.flower.loadbalancer.server.port: "5555"
```

Optional whoami check (helpful before switching app DNS):

```yaml
services:
  whoami:
    image: traefik/whoami:v1.10.3
    restart: unless-stopped
    networks: [traefik-proxy]
    labels:
      traefik.enable: "true"
      traefik.docker.network: traefik-proxy
      traefik.http.routers.whoami.rule: "Host(`whoami.edcopo.info`)"
      traefik.http.routers.whoami.entrypoints: "websecure"
      traefik.http.routers.whoami.tls: "true"
      traefik.http.routers.whoami.tls.certresolver: "cloudflare"
      traefik.http.services.whoami.loadbalancer.server.port: "80"
```

## 4) DNS and environment checks

- FastAPI CORS: `.env` or compose already sets `CORS_ORIGINS=https://pdf.edcopo.info,https://apipdf.edcopo.info` — keep this.
- Frontend build args and env already point to the right public URLs — no change needed.
- Create/verify DNS A/AAAA records for `pdf.edcopo.info`, `apipdf.edcopo.info` (and `flower.edcopo.info` if used) → Traefik host IP.

## 5) Deploy sequence

1. Ensure the external network exists on the host running Traefik:
   ```bash
   docker network create traefik-proxy || true
   ```
2. Stop Caddy (on this stack only):
   ```bash
   docker compose stop caddy || true
   ```
3. Bring up or recreate services so they join `traefik-proxy`:
   ```bash
   docker compose up -d api web monitor
   # optional
   docker compose up -d whoami
   ```
4. Verify routes and certs in Traefik dashboard (routers/services healthy).
5. Test via curl:
   ```bash
   curl -I https://apipdf.edcopo.info/health
   curl -I https://pdf.edcopo.info/
   ```
6. Remove host port publishes from compose (hardening) and redeploy:
   ```bash
   # Remove ports sections for api/web/monitor in docker-compose.yml
   docker compose up -d
   ```

## Troubleshooting

- 404 from Traefik:
  - Wrong router rule (Host) or service not on `traefik-proxy` network
  - `loadbalancer.server.port` doesn’t match container’s internal port
- Cert not issued:
  - Traefik ACME misconfig — confirm your central Traefik has `cloudflare` resolver and valid `CF_DNS_API_TOKEN`
- CORS issues:
  - Keep server-side CORS in FastAPI; optional Traefik CORS middleware can complement but not replace it

## Rollback

- Re-enable host `ports:` on `api`/`web`/`monitor` and access via server IP/ports
- Or restore the `caddy` service and `docker compose up -d caddy`

## Minimal diff checklist

- [ ] Add `traefik-proxy` to `networks` (external: true)
- [ ] Remove `caddy` service
- [ ] For `api`/`web`/`monitor`:
  - [ ] Join `traefik-proxy` network (in addition to `pdftr_default`)
  - [ ] Add Traefik labels (router rule, entrypoints, tls, certresolver, service port)
  - [ ] Remove host `ports:` after verification
- [ ] Update DNS to Traefik host
- [ ] Deploy and validate

---

Appendix: Example consolidated service excerpts

```yaml
services:
  api:
    build: ./backend
    environment:
      - DATABASE_URL=postgresql://user:password@db/pdftr
      - REDIS_URL=redis://cache:6379/0
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ENVIRONMENT=production
      - DEBUG=false
      - CORS_ORIGINS=https://pdf.edcopo.info,https://apipdf.edcopo.info
    networks: [pdftr_default, traefik-proxy]
    labels:
      traefik.enable: "true"
      traefik.docker.network: traefik-proxy
      traefik.http.routers.api.rule: "Host(`apipdf.edcopo.info`)"
      traefik.http.routers.api.entrypoints: "websecure"
      traefik.http.routers.api.tls: "true"
      traefik.http.routers.api.tls.certresolver: "cloudflare"
      traefik.http.services.api.loadbalancer.server.port: "8000"

  web:
    build:
      context: ./frontend
      args:
        NEXT_PUBLIC_API_URL: https://apipdf.edcopo.info
        NEXT_PUBLIC_APP_URL: https://pdf.edcopo.info
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_API_URL=https://apipdf.edcopo.info
      - NEXT_PUBLIC_APP_URL=https://pdf.edcopo.info
    networks: [pdftr_default, traefik-proxy]
    labels:
      traefik.enable: "true"
      traefik.docker.network: traefik-proxy
      traefik.http.routers.web.rule: "Host(`pdf.edcopo.info`)"
      traefik.http.routers.web.entrypoints: "websecure"
      traefik.http.routers.web.tls: "true"
      traefik.http.routers.web.tls.certresolver: "cloudflare"
      traefik.http.services.web.loadbalancer.server.port: "3000"

  monitor:
    build: ./backend
    command: celery -A app.workers.celery_worker.celery_app flower --port=5555 --broker=redis://cache:6379/0
    environment:
      - REDIS_URL=redis://cache:6379/0
      - FLOWER_BASIC_AUTH=admin:${FLOWER_PASSWORD}
    networks: [pdftr_default, traefik-proxy]
    labels:
      traefik.enable: "true"
      traefik.docker.network: traefik-proxy
      traefik.http.routers.flower.rule: "Host(`flower.edcopo.info`)"
      traefik.http.routers.flower.entrypoints: "websecure"
      traefik.http.routers.flower.tls: "true"
      traefik.http.routers.flower.tls.certresolver: "cloudflare"
      traefik.http.routers.flower.middlewares: "studio-auth@file"
      traefik.http.services.flower.loadbalancer.server.port: "5555"

networks:
  traefik-proxy:
    external: true
  pdftr_default:
    driver: bridge
```
