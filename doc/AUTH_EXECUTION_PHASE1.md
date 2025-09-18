# Phase 1 Execution Guide: Basic Authelia Setup

## Overview
**Goal**: Replace broken Traefik basic auth with working Authelia authentication for Flower dashboard
**Timeline**: 1 week (8 development hours)
**Success**: Secure, reliable access to Flower monitoring interface

## Prerequisites Checklist

- [ ] Docker Compose environment working
- [ ] Traefik reverse proxy operational
- [ ] SSL certificates configured for *.edcopo.info
- [ ] Redis service available for session storage
- [ ] SSH access to production server
- [ ] Backup of current docker-compose.yml

## Implementation Steps

### Step 1: Create Authelia Configuration
**Time**: 1 hour

**1.1 Create Directory Structure**
```bash
mkdir -p authelia/config
mkdir -p authelia/users
```

**1.2 Create Main Configuration File**
Create `authelia/config/configuration.yml`:
```yaml
# Authelia Configuration - Phase 1 (Minimal)
server:
  host: 0.0.0.0
  port: 9091
  path: ""

log:
  level: info
  file_path: /config/authelia.log

authentication_backend:
  password_reset:
    disable: true
  file:
    path: /config/users_database.yml
    password:
      algorithm: argon2id
      iterations: 1
      salt_length: 16
      parallelism: 8
      memory: 64

access_control:
  default_policy: deny
  rules:
    # Allow access to Authelia portal
    - domain: auth.edcopo.info
      policy: bypass

    # Require authentication for Flower
    - domain: flower.edcopo.info
      policy: one_factor

    # Future services (initially deny)
    - domain: "*.edcopo.info"
      policy: deny

session:
  name: authelia_session
  domain: edcopo.info
  same_site: lax
  expiration: 1h
  inactivity: 5m
  remember_me_duration: 1M
  redis:
    host: cache
    port: 6379
    database_index: 1

regulation:
  max_retries: 3
  find_time: 2m
  ban_time: 5m

storage:
  local:
    path: /config/db.sqlite3

notifier:
  filesystem:
    filename: /config/notification.txt

theme: dark
```

**1.3 Create User Database**
Create `authelia/config/users_database.yml`:
```yaml
# User Database - Phase 1
users:
  admin:
    displayname: "Platform Administrator"
    password: "$argon2id$v=19$m=65536,t=3,p=4$PLACEHOLDER_HASH"
    email: admin@edcopo.info
    groups:
      - admins
      - dev

groups:
  - name: admins
    description: "Platform Administrators"
  - name: dev
    description: "Developers"
  - name: users
    description: "Regular Users"
```

### Step 2: Generate Secure Password Hash
**Time**: 15 minutes

**2.1 Generate Password Hash**
```bash
# Generate secure password hash
docker run --rm authelia/authelia:4.39 authelia crypto hash generate argon2 --password 'YourSecurePassword123!'
```

**2.2 Update User Database**
Replace `PLACEHOLDER_HASH` in users_database.yml with generated hash.

### Step 3: Update Docker Compose
**Time**: 30 minutes

**3.1 Add Authelia Service**
Add to `docker-compose.yml`:
```yaml
services:
  # ... existing services ...

  authelia:
    image: authelia/authelia:4.39
    container_name: authelia
    volumes:
      - ./authelia/config:/config
    networks:
      - pdftr_default
      - traefik-proxy
    restart: unless-stopped
    environment:
      - AUTHELIA_JWT_SECRET=${AUTHELIA_JWT_SECRET}
      - AUTHELIA_SESSION_SECRET=${AUTHELIA_SESSION_SECRET}
      - AUTHELIA_STORAGE_ENCRYPTION_KEY=${AUTHELIA_STORAGE_ENCRYPTION_KEY}
    labels:
      traefik.enable: "true"
      traefik.docker.network: "traefik-proxy"
      traefik.http.routers.authelia.rule: "Host(`auth.edcopo.info`)"
      traefik.http.routers.authelia.entrypoints: "websecure"
      traefik.http.routers.authelia.tls: "true"
      traefik.http.routers.authelia.tls.certresolver: "cloudflare"
      traefik.http.services.authelia.loadbalancer.server.port: "9091"
      # Forward auth middleware
      traefik.http.middlewares.authelia.forwardauth.address: "http://authelia:9091/api/authz/forward-auth"
      traefik.http.middlewares.authelia.forwardauth.trustForwardHeader: "true"
      traefik.http.middlewares.authelia.forwardauth.authResponseHeaders: "Remote-User,Remote-Groups,Remote-Name,Remote-Email"
```

**3.2 Update Flower Service**
Modify Flower service in `docker-compose.yml`:
```yaml
  monitor:
    build: ./backend
    command: celery -A app.workers.celery_worker.celery_app flower --port=5555
    environment:
      - REDIS_URL=redis://cache:6379/0
      - CELERY_BROKER_URL=redis://cache:6379/0
    depends_on:
      - cache
      - worker
    networks:
      - pdftr_default
      - traefik-proxy
    restart: unless-stopped
    labels:
      traefik.enable: "true"
      traefik.docker.network: "traefik-proxy"
      traefik.http.routers.pdftr-flower.rule: "Host(`flower.edcopo.info`)"
      traefik.http.routers.pdftr-flower.entrypoints: "websecure"
      traefik.http.routers.pdftr-flower.tls: "true"
      traefik.http.routers.pdftr-flower.tls.certresolver: "cloudflare"
      traefik.http.routers.pdftr-flower.middlewares: "authelia@docker"
      traefik.http.services.pdftr-flower.loadbalancer.server.port: "5555"
```

### Step 4: Environment Variables
**Time**: 15 minutes

**4.1 Generate Secrets**
```bash
# Generate random secrets
openssl rand -hex 32  # For AUTHELIA_JWT_SECRET
openssl rand -hex 32  # For AUTHELIA_SESSION_SECRET
openssl rand -hex 32  # For AUTHELIA_STORAGE_ENCRYPTION_KEY
```

**4.2 Update .env File**
Add to `.env`:
```env
# Authelia Secrets
AUTHELIA_JWT_SECRET=your_jwt_secret_here
AUTHELIA_SESSION_SECRET=your_session_secret_here
AUTHELIA_STORAGE_ENCRYPTION_KEY=your_storage_encryption_key_here
```

### Step 5: Deploy and Test
**Time**: 30 minutes

**5.1 Deploy Services**
```bash
# Start Authelia first
docker-compose up -d authelia

# Wait for startup and check logs
docker-compose logs authelia

# Update Flower service
docker-compose up -d monitor
```

**5.2 DNS Configuration**
Ensure `auth.edcopo.info` points to your server IP.

**5.3 Test Authentication Flow**
1. Visit https://flower.edcopo.info
2. Should redirect to https://auth.edcopo.info/
3. Login with admin credentials
4. Should redirect back to Flower dashboard
5. Verify session persists across browser refresh

### Step 6: Verification and Documentation
**Time**: 30 minutes

**6.1 Functional Testing**
- [ ] Flower dashboard accessible with authentication
- [ ] Login redirects work correctly
- [ ] Session persists for 1 hour
- [ ] Logout functionality works
- [ ] Invalid credentials are rejected
- [ ] Account lockout after 3 failed attempts

**6.2 Security Testing**
- [ ] Direct access to Flower without auth blocked
- [ ] Authelia admin interface accessible
- [ ] Session cookies are secure and httpOnly
- [ ] No authentication bypass possible

**6.3 Create Documentation**
Document the following:
- Admin login credentials (secure storage)
- Configuration file locations
- Troubleshooting common issues
- Backup and recovery procedures

## Environment Variables Reference

```env
# Required for Phase 1
AUTHELIA_JWT_SECRET=<32-character-hex-string>
AUTHELIA_SESSION_SECRET=<32-character-hex-string>
AUTHELIA_STORAGE_ENCRYPTION_KEY=<32-character-hex-string>

# Optional - defaults are suitable for Phase 1
AUTHELIA_LOG_LEVEL=info
AUTHELIA_SESSION_EXPIRATION=1h
AUTHELIA_SESSION_INACTIVITY=5m
```

## File Structure After Phase 1

```
pdf-translation-platform/
├── docker-compose.yml          # Updated with Authelia service
├── .env                        # Updated with Authelia secrets
├── authelia/
│   └── config/
│       ├── configuration.yml   # Main Authelia config
│       ├── users_database.yml  # User accounts
│       ├── authelia.log        # Application logs
│       ├── db.sqlite3          # Session storage
│       └── notification.txt    # Notification log
└── doc/
    ├── AUTH_EXECUTION_PHASE1.md # This guide
    └── AUTH_TROUBLESHOOTING.md  # Common issues
```

## Troubleshooting Guide

### Common Issues

**Issue**: Authelia container won't start
**Solution**: Check configuration.yml syntax with YAML validator

**Issue**: Redirect loop between Flower and Authelia
**Solution**: Verify domain configuration and middleware setup

**Issue**: Sessions don't persist
**Solution**: Check Redis connection and session configuration

**Issue**: Cannot access auth.edcopo.info
**Solution**: Verify DNS configuration and SSL certificate

### Log Analysis

**Check Authelia logs:**
```bash
docker-compose logs authelia
```

**Check Traefik logs:**
```bash
docker-compose logs traefik
```

**Check Flower logs:**
```bash
docker-compose logs monitor
```

### Recovery Procedures

**Rollback to No Authentication:**
1. Remove `middlewares: "authelia@docker"` from Flower service
2. Run `docker-compose up -d monitor`
3. Flower will be accessible without authentication

**Reset Admin Password:**
1. Generate new password hash
2. Update `authelia/config/users_database.yml`
3. Restart Authelia: `docker-compose restart authelia`

## Success Criteria Checklist

- [ ] Authelia container running and healthy
- [ ] auth.edcopo.info accessible and showing login page
- [ ] flower.edcopo.info requires authentication
- [ ] Admin user can login successfully
- [ ] Session persists for 1 hour
- [ ] Logout functionality works
- [ ] No authentication bypass possible
- [ ] Configuration documented and backed up

## Next Steps After Phase 1

1. **Test with team members** - Get feedback on login experience
2. **Monitor performance** - Check authentication response times
3. **Plan Phase 2** - Prepare for additional service protection
4. **Create user accounts** - Add team member accounts as needed
5. **Backup procedures** - Document backup and recovery

---

*This execution guide provides step-by-step instructions for implementing basic Authelia authentication to solve the immediate Flower access problem.*