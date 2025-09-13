# Production Deployment Guide
# PDF Translation Platform - edcopo.info

## 🌐 Subdomain Configuration

### Recommended Subdomains
- **`pdf.edcopo.info`** - Main application (Frontend + API)
- **`apipdf.edcopo.info`** - API-only access
- **`adminpdf.edcopo.info`** - Admin panel (Celery Flower)
- **`docspdf.edcopo.info`** - API documentation

## 🚀 Quick Deployment Steps

### 1. DNS Configuration
Configure these DNS records for your domain:

```bash
# A Records (point to your server IP)
pdf.edcopo.info        A    YOUR_SERVER_IP
apipdf.edcopo.info     A    YOUR_SERVER_IP
adminpdf.edcopo.info   A    YOUR_SERVER_IP
docspdf.edcopo.info   A    YOUR_SERVER_IP

# CNAME Records (alternative)
pdf.edcopo.info        CNAME    edcopo.info
apipdf.edcopo.info     CNAME    edcopo.info
adminpdf.edcopo.info   CNAME    edcopo.info
docspdf.edcopo.info   CNAME    edcopo.info
```

### 2. Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create necessary directories
mkdir -p logs backups uploads
```

### 3. Environment Setup
```bash
# Copy production environment template
cp env.prod.example .env.prod

# Edit production environment
nano .env.prod

# Generate secure passwords
openssl rand -base64 32  # For SECRET_KEY
openssl rand -base64 32  # For SESSION_SECRET
openssl rand -base64 32  # For JWT_SECRET
openssl rand -base64 32  # For ENCRYPTION_KEY
```

### 4. Production Deployment
```bash
# Start production services
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 5. SSL Certificate Verification
```bash
# Check if certificates are issued
docker-compose -f docker-compose.prod.yml logs caddy

# Test HTTPS endpoints
curl -I https://pdf.edcopo.info
curl -I https://apipdf.edcopo.info
curl -I https://adminpdf.edcopo.info
curl -I https://docspdf.edcopo.info
```

## 🔧 Configuration Details

### Caddy Configuration
The `Caddyfile` includes:
- **Automatic HTTPS** with Let's Encrypt certificates
- **Rate limiting** for API protection
- **Security headers** for enhanced security
- **Reverse proxy** routing to appropriate services
- **Logging** for monitoring and debugging

### Docker Compose Services
- **caddy**: Reverse proxy and HTTPS termination
- **postgres**: Database with health checks
- **redis**: Cache and message broker
- **backend**: FastAPI application
- **frontend**: Next.js application
- **celery-worker**: Background task processing
- **flower**: Celery monitoring dashboard
- **db-backup**: Automated database backups

### Security Features
- **HTTPS everywhere** with automatic certificate renewal
- **Rate limiting** to prevent abuse
- **Security headers** (HSTS, CSP, etc.)
- **Basic authentication** for admin panel
- **CORS configuration** for API access
- **Input validation** and sanitization

## 📊 Monitoring & Maintenance

### Health Checks
```bash
# Check all services
docker-compose -f docker-compose.prod.yml ps

# Check specific service logs
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs celery-worker

# Monitor resource usage
docker stats
```

### Backup Management
```bash
# Manual database backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U user pdftr > backup_$(date +%Y%m%d_%H%M%S).sql

# Check backup directory
ls -la backups/

# Restore from backup
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U user pdftr < backup_file.sql
```

### Log Management
```bash
# View application logs
tail -f logs/app.log

# View Caddy logs
tail -f logs/pdf.log

# Rotate logs (add to crontab)
0 0 * * * find logs/ -name "*.log" -mtime +7 -delete
```

## 🔄 Updates & Maintenance

### Application Updates
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart services
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Zero-downtime deployment
docker-compose -f docker-compose.prod.yml up -d --no-deps backend frontend
```

### Certificate Renewal
Caddy automatically handles certificate renewal, but you can check:
```bash
# Check certificate status
docker-compose -f docker-compose.prod.yml exec caddy caddy list-certificates

# Force certificate renewal
docker-compose -f docker-compose.prod.yml exec caddy caddy reload --config /etc/caddy/Caddyfile
```

## 🚨 Troubleshooting

### Common Issues

#### 1. SSL Certificate Issues
```bash
# Check DNS resolution
nslookup pdf.tonmastery.xyz

# Check port accessibility
telnet YOUR_SERVER_IP 80
telnet YOUR_SERVER_IP 443

# Check Caddy logs
docker-compose -f docker-compose.prod.yml logs caddy
```

#### 2. Service Not Starting
```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# Check service logs
docker-compose -f docker-compose.prod.yml logs SERVICE_NAME

# Restart specific service
docker-compose -f docker-compose.prod.yml restart SERVICE_NAME
```

#### 3. Database Connection Issues
```bash
# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres

# Test database connection
docker-compose -f docker-compose.prod.yml exec backend python -c "from core.database import engine; print(engine.execute('SELECT 1').scalar())"
```

#### 4. File Upload Issues
```bash
# Check upload directory permissions
ls -la uploads/

# Fix permissions
sudo chown -R 1000:1000 uploads/
sudo chmod -R 755 uploads/
```

### Performance Optimization

#### 1. Database Optimization
```bash
# Check database size
docker-compose -f docker-compose.prod.yml exec postgres psql -U user -d pdftr -c "SELECT pg_size_pretty(pg_database_size('pdftr'));"

# Analyze query performance
docker-compose -f docker-compose.prod.yml exec postgres psql -U user -d pdftr -c "ANALYZE;"
```

#### 2. Redis Optimization
```bash
# Check Redis memory usage
docker-compose -f docker-compose.prod.yml exec redis redis-cli info memory

# Clear Redis cache if needed
docker-compose -f docker-compose.prod.yml exec redis redis-cli FLUSHALL
```

#### 3. Application Scaling
```bash
# Scale Celery workers
docker-compose -f docker-compose.prod.yml up -d --scale celery-worker=4

# Scale backend (if using load balancer)
docker-compose -f docker-compose.prod.yml up -d --scale backend=2
```

## 📈 Performance Monitoring

### Key Metrics to Monitor
- **Response Time**: < 2 seconds for API calls
- **Throughput**: > 100 requests/minute
- **Error Rate**: < 1%
- **Uptime**: > 99.9%
- **Resource Usage**: CPU < 80%, Memory < 80%

### Monitoring Tools
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs

# Monitor system resources
htop
iotop
nethogs

# Monitor Docker resources
docker stats
```

## 🔐 Security Checklist

### Pre-Deployment Security
- [ ] Change all default passwords
- [ ] Generate secure random keys
- [ ] Configure firewall rules
- [ ] Enable fail2ban
- [ ] Set up log monitoring
- [ ] Configure automatic security updates

### Post-Deployment Security
- [ ] Test SSL certificates
- [ ] Verify security headers
- [ ] Test rate limiting
- [ ] Check admin panel access
- [ ] Monitor failed login attempts
- [ ] Regular security updates

## 📞 Support & Maintenance

### Regular Maintenance Tasks
- **Daily**: Check service status and logs
- **Weekly**: Review error logs and performance metrics
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Review and rotate secrets

### Emergency Procedures
- **Service Down**: Check logs, restart services, check resources
- **SSL Issues**: Verify DNS, check Caddy logs, renew certificates
- **Database Issues**: Check connections, restore from backup
- **Performance Issues**: Scale services, optimize queries, clear cache

---

*This deployment guide ensures a production-ready PDF translation platform with automatic HTTPS, monitoring, and security features.*
