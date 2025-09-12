#!/bin/bash

# PDF Translation Platform - Production Deployment Script
# For tonmastery.xyz domain

set -e  # Exit on any error

echo "🚀 Starting PDF Translation Platform Production Deployment"
echo "Domain: edcopo.info"
echo "Subdomain: pdf.edcopo.info"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root for security reasons"
   exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env.prod exists
if [ ! -f ".env.prod" ]; then
    print_warning ".env.prod not found. Creating from template..."
    if [ -f "env.prod.example" ]; then
        cp env.prod.example .env.prod
        print_warning "Please edit .env.prod with your production settings before continuing."
        print_warning "Especially update:"
        print_warning "  - POSTGRES_PASSWORD"
        print_warning "  - SECRET_KEY"
        print_warning "  - FLOWER_PASSWORD"
        print_warning "  - CADDY_EMAIL"
        read -p "Press Enter to continue after editing .env.prod..."
    else
        print_error "env.prod.example not found. Cannot create .env.prod"
        exit 1
    fi
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs backups uploads
print_success "Directories created"

# Check DNS resolution
print_status "Checking DNS resolution for subdomains..."
SUBDOMAINS=("pdf.edcopo.info" "apipdf.edcopo.info" "adminpdf.edcopo.info" "docspdf.edcopo.info")

for subdomain in "${SUBDOMAINS[@]}"; do
    if nslookup "$subdomain" > /dev/null 2>&1; then
        print_success "DNS resolved for $subdomain"
    else
        print_warning "DNS not resolved for $subdomain - make sure DNS is configured"
    fi
done

# Check if ports are available
print_status "Checking if required ports are available..."
PORTS=(80 443)

for port in "${PORTS[@]}"; do
    if netstat -tuln | grep ":$port " > /dev/null; then
        print_warning "Port $port is already in use. Make sure no other web server is running."
    else
        print_success "Port $port is available"
    fi
done

# Build and start services
print_status "Building Docker images..."
docker-compose -f docker-compose.prod.yml build

print_status "Starting production services..."
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# Wait for services to start
print_status "Waiting for services to start..."
sleep 30

# Check service status
print_status "Checking service status..."
docker-compose -f docker-compose.prod.yml ps

# Check if services are healthy
print_status "Checking service health..."

# Check backend health
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Backend service is healthy"
else
    print_warning "Backend service health check failed"
fi

# Check frontend health
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    print_success "Frontend service is healthy"
else
    print_warning "Frontend service health check failed"
fi

# Check Caddy logs for SSL certificate
print_status "Checking SSL certificate status..."
sleep 10  # Give Caddy time to get certificates

if docker-compose -f docker-compose.prod.yml logs caddy | grep -q "certificate obtained successfully"; then
    print_success "SSL certificates obtained successfully"
else
    print_warning "SSL certificate status unclear. Check Caddy logs:"
    docker-compose -f docker-compose.prod.yml logs caddy | tail -20
fi

# Test HTTPS endpoints
print_status "Testing HTTPS endpoints..."
ENDPOINTS=("https://pdf.edcopo.info" "https://apipdf.edcopo.info" "https://adminpdf.edcopo.info" "https://docspdf.edcopo.info")

for endpoint in "${ENDPOINTS[@]}"; do
    if curl -I -k "$endpoint" > /dev/null 2>&1; then
        print_success "HTTPS endpoint accessible: $endpoint"
    else
        print_warning "HTTPS endpoint not accessible: $endpoint"
    fi
done

# Display deployment summary
echo ""
echo "🎉 Deployment Summary"
echo "===================="
echo ""
echo "🌐 Access URLs:"
echo "  Main Application: https://pdf.edcopo.info"
echo "  API Endpoint:     https://apipdf.edcopo.info"
echo "  Admin Panel:      https://adminpdf.edcopo.info"
echo "  API Docs:         https://docspdf.edcopo.info"
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.prod.yml ps
echo ""
echo "📝 Useful Commands:"
echo "  View logs:        docker-compose -f docker-compose.prod.yml logs -f"
echo "  Restart services: docker-compose -f docker-compose.prod.yml restart"
echo "  Stop services:    docker-compose -f docker-compose.prod.yml down"
echo "  Update services:  docker-compose -f docker-compose.prod.yml pull && docker-compose -f docker-compose.prod.yml up -d"
echo ""
echo "🔧 Next Steps:"
echo "  1. Test the application by uploading a PDF"
echo "  2. Check admin panel for Celery worker status"
echo "  3. Monitor logs for any issues"
echo "  4. Set up monitoring and alerting"
echo ""
print_success "Deployment completed! Your PDF translation platform is now live at https://pdf.edcopo.info"
