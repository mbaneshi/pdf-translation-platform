# Migrating Reverse Proxy: Caddy → Traefik

This guide walks you through replacing Caddy with Traefik for TLS termination, reverse proxy, and routing in this project. It is tailored to the current `docker-compose.yml` (which defines `api` on port 8000 and `web` on port 3000, plus `monitor` on 5555) and the production domains:

- Frontend: `https://pdf.edcopo.info`
- Backend API: `https://apipdf.edcopo.info`
- Optional UIs: `https://flower.edcopo.info`, `https://grafana.edcopo.info`, `https://jaeger.edcopo.info`

## Prerequisites

- DNS: `A/AAAA` records for the domains above point to your Docker host.
- Cloudflare API Token: `CF_DNS_API_TOKEN` with Zone.DNS Edit + Zone Read for the zone.
- Open ports: `80` and `443` free on the host (stop Caddy before starting Traefik).
- Environment: `.env` contains:
  - `CF_DNS_API_TOKEN=...`
  - `TRAEFIK_ACME_EMAIL=admin@example.com` (email used for ACME/Let’s Encrypt)

## 1) Add Traefik configuration files

Create `traefik.yml` (static config) and `dynamic.yml` (dynamic middlewares) at the repo root.

traefik.yml:

```yaml
# Static configuration
entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
          permanent: true
  websecure:
    address: ":443"

providers:
  docker:
    exposedByDefault: false
  file:
    filename: /dynamic.yml
    watch: true

certificatesResolvers:
  cloudflare:
    acme:
      email: ${TRAEFIK_ACME_EMAIL:-admin@example.com}
      storage: /acme.json
      dnsChallenge:
        provider: cloudflare
        # Use public resolvers to avoid corporate DNS issues
        resolvers:
          - "1.1.1.1:53"
          - "8.8.8.8:53"

log:
  level: INFO
accessLog: {}

# Optional telemetry hooks
metrics:
  prometheus: {}
# tracing:
#   jaeger:
#     localAgentHostPort: jaeger:6831
# api:
#   dashboard: true  # expose via router + auth in dynamic.yml
```

dynamic.yml:

```yaml
# Dynamic configuration (middlewares, TLS options)
http:
  middlewares:
    secure-headers:
      headers:
        sslRedirect: true
        stsSeconds: 31536000
        stsIncludeSubdomains: true
        stsPreload: true
        frameDeny: true
        browserXSSFilter: true
        contentTypeNosniff: true
        referrerPolicy: "no-referrer-when-downgrade"
        permissionsPolicy: "geolocation=(), microphone=()"
    cors-headers:
      headers:
        accessControlAllowMethods:
          - GET
          - POST
          - PUT
          - PATCH
          - DELETE
          - OPTIONS
        accessControlAllowHeaders:
          - "*"
        accessControlAllowOriginList:
          - "https://pdf.edcopo.info"
          - "https://apipdf.edcopo.info"
        accessControlAllowCredentials: true
    # Optional: basic auth for dashboards
    studio-auth:
      basicAuth:
        # Replace with a real htpasswd hash (see appendix)
        users:
          - "admin:$apr1$REPLACE_WITH_VALID_HTPASSWD_HASH"

tls:
  options:
    default:
      minVersion: VersionTLS12
```

Create and secure ACME storage file (first time only):

```bash
# From repo root
touch acme.json
chmod 600 acme.json
```

## 2) Replace Caddy service with Traefik in docker-compose.yml

Remove the `caddy` service from `docker-compose.yml` and add the following `traefik` service. Keep Traefik on the same network as your app services (the default `pdftr_default`).

```yaml
services:
  traefik:
    image: traefik:v2.11
    container_name: traefik
    restart: unless-stopped
    environment:
      CF_DNS_API_TOKEN: ${CF_DNS_API_TOKEN}
    ports:
      - "80:80"
      - "443:443"
    command:
      - --configFile=/traefik.yml
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik.yml:/traefik.yml:ro
      - ./dynamic.yml:/dynamic.yml:ro
      - ./acme.json:/acme.json
    networks:
      - pdftr_default
```

## 3) Add Traefik labels to exposed services

Attach each exposed service to the same network as Traefik and add labels. You can initially keep host-port publishing for troubleshooting and remove it after verification.

Backend API (`api`, internal port 8000):

```yaml
services:
  api:
    # ...existing config...
    labels:
      traefik.enable: "true"
      traefik.http.routers.api.rule: "Host(`apipdf.edcopo.info`)"
      traefik.http.routers.api.entrypoints: "websecure"
      traefik.http.routers.api.tls: "true"
      traefik.http.routers.api.tls.certresolver: "cloudflare"
      traefik.http.routers.api.middlewares: "cors-headers@file,secure-headers@file"
      traefik.http.services.api.loadbalancer.server.port: "8000"
    networks:
      - pdftr_default
    # Optional hardening after cutover: remove "8000:8000"
    # ports: ["8000:8000"]
```

Frontend (`web`, internal port 3000):

```yaml
services:
  web:
    # ...existing config...
    labels:
      traefik.enable: "true"
      traefik.http.routers.web.rule: "Host(`pdf.edcopo.info`)"
      traefik.http.routers.web.entrypoints: "websecure"
      traefik.http.routers.web.tls: "true"
      traefik.http.routers.web.tls.certresolver: "cloudflare"
      traefik.http.routers.web.middlewares: "secure-headers@file"
      traefik.http.services.web.loadbalancer.server.port: "3000"
    networks:
      - pdftr_default
    # Optional hardening after cutover: remove "3000:3000"
    # ports: ["3000:3000"]
```

Flower (`monitor`, internal port 5555) behind auth:

```yaml
services:
  monitor:
    # ...existing config...
    labels:
      traefik.enable: "true"
      traefik.http.routers.flower.rule: "Host(`flower.edcopo.info`)"
      traefik.http.routers.flower.entrypoints: "websecure"
      traefik.http.routers.flower.tls: "true"
      traefik.http.routers.flower.tls.certresolver: "cloudflare"
      traefik.http.routers.flower.middlewares: "studio-auth@file,secure-headers@file"
      traefik.http.services.flower.loadbalancer.server.port: "5555"
    networks:
      - pdftr_default
    # Optional hardening after cutover: remove "5555:5555"
    # ports: ["5555:5555"]
```

Optional sanity check container:

```yaml
services:
  whoami:
    image: traefik/whoami:v1.10.3
    restart: unless-stopped
    networks:
      - pdftr_default
    labels:
      traefik.enable: "true"
      traefik.http.routers.whoami.rule: "Host(`whoami.edcopo.info`)"
      traefik.http.routers.whoami.entrypoints: "websecure"
      traefik.http.routers.whoami.tls: "true"
      traefik.http.routers.whoami.tls.certresolver: "cloudflare"
      traefik.http.services.whoami.loadbalancer.server.port: "80"
```

> Note: You can apply the same label pattern to Grafana, Prometheus, and Jaeger if you decide to expose them publicly.

## 4) Cutover procedure

1. Stop Caddy (free ports 80/443):
   ```bash
   docker compose stop caddy || true
   ```
2. Ensure config files exist and permissions are set:
   ```bash
   ls -l traefik.yml dynamic.yml && [ -f acme.json ] || touch acme.json
   chmod 600 acme.json
   ```
3. Start Traefik first, then the app services:
   ```bash
   docker compose up -d traefik
   docker compose up -d api web monitor
   ```
4. Watch Traefik logs for ACME + router readiness:
   ```bash
   docker compose logs -f traefik
   ```
5. Verify endpoints:
   ```bash
   curl -I https://apipdf.edcopo.info/health
   curl -I https://pdf.edcopo.info/
   # If whoami is enabled
   curl -I https://whoami.edcopo.info/
   ```
6. Optional hardening: remove direct host ports from `api`, `web`, and `monitor` in compose once routing works.

## 5) Optional: Observability and dashboard

- Traefik dashboard: enable `api.dashboard: true` in `traefik.yml`, then add a router (e.g., `traefik.yourdomain`) secured by `studio-auth@file` in `dynamic.yml`.
- Prometheus: `metrics.prometheus: {}` already included. Add a scrape job in `prometheus.yml`:

  ```yaml
  scrape_configs:
    - job_name: 'traefik'
      static_configs:
        - targets: ['traefik:8080']
  ```

- Tracing: uncomment Jaeger settings in `traefik.yml` and point to your `jaeger` service.

## 6) Rollback plan

- To revert to Caddy: stop Traefik and bring Caddy back up.
  ```bash
  docker compose down traefik || true
  docker compose up -d caddy
  ```
- Leave `traefik.yml`, `dynamic.yml`, and `acme.json` in place for future cutovers.

## 7) Housekeeping

- Update `start.sh` to include `traefik` instead of `caddy` if you automate startup.
- Remove or archive `Caddyfile` and related references in `README.md` once migration is complete.

## Appendix

- Generate htpasswd hash for `studio-auth` middleware:
  ```bash
  docker run --rm httpd:2-alpine htpasswd -nbB admin 'yourPassword' | sed -e 's/\$/\$\$/g'
  # Replace the value in dynamic.yml: users: [ "admin:..." ]
  ```
- Common pitfalls:
  - ACME fails with Cloudflare: ensure `CF_DNS_API_TOKEN` has Zone DNS Edit on the correct zone and the token is present in the container env.
  - 404s from Traefik: confirm labels and `loadbalancer.server.port` match the container’s internal port (not the published host port).
  - Mixed content/CORS: keep FastAPI `CORS_ORIGINS` configured (already set) and optionally use the Traefik `cors-headers` middleware.

