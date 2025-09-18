# Advanced PDF Translation Platform

A comprehensive production-ready system for translating PDF documents from English to Persian using OpenAI's GPT models.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js       │    │   FastAPI       │    │   PostgreSQL    │
│   Frontend      │◄──►│   Backend       │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              │
                              ▼
                        ┌─────────────────┐    ┌─────────────────┐
                        │   Redis         │◄──►│   Celery        │
                        │   Message Broker│    │   Workers       │
                        └─────────────────┘    └─────────────────┘
                              │                       │
                              │                       │
                              └───────────────────────┘
                                      │
                                      ▼
                                ┌─────────────────┐
                                │   OpenAI API    │
                                └─────────────────┘
```

## Features

- ✅ **Full PDF Processing**: Extract text from PDFs using PyMuPDF
- ✅ **Database Storage**: PostgreSQL for persistent storage of documents and translations
- ✅ **Test Translation**: Translate individual pages for testing before full processing
- ✅ **Async Processing**: Celery workers for scalable background translation
- ✅ **REST API**: Comprehensive FastAPI backend with automatic documentation
- ✅ **Modern Frontend**: Next.js with Tailwind CSS and React components
- ✅ **Docker Ready**: Complete containerization with Docker Compose
- ✅ **Monitoring**: Celery Flower for task monitoring
- ✅ **Production Ready**: Health checks, error handling, and proper logging

## Quick Start

### Prerequisites

- Docker and Docker Compose
- OpenAI API key

### 1. Environment Setup

Copy the environment template:
```bash
cp env.example .env
```

Edit `.env` and add your OpenAI API key:
```env
OPENAI_API_KEY=your_actual_openai_api_key_here
```

### 2. Start the Infrastructure

```bash
# Start database and Redis
docker-compose up -d postgres redis

# Wait for services to be healthy, then start the application
docker-compose up -d backend celery-worker flower
```

### 3. Access the Application

- **Frontend**: http://localhost:3000 (when running Next.js)
- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Celery Monitoring**: http://localhost:5555

## Development Setup

### Backend Development

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

### Database Migrations (Alembic)

This repository includes Alembic for schema migrations.

1. Configure your database URL in `.env` (or export `DATABASE_URL`).
2. Run migrations:
```bash
cd backend
alembic upgrade head
```

The current migration adds a `metadata` JSON column to `pdf_pages` for per-page processing results.
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Running Celery Worker

```bash
cd backend
celery -A app.workers.celery_worker.celery_app worker --loglevel=info
```

## API Endpoints

### Documents

- `POST /api/documents/upload` - Upload PDF document
- `GET /api/documents/{id}` - Get document details
- `GET /api/documents/{id}/pages` - Get all pages for a document
- `POST /api/documents/{id}/translate` - Start full document translation
- `POST /api/documents/{id}/pages/{page_number}/test` - Test translate a single page

### Health Check

- `GET /health` - API health status

## Usage Workflow

1. **Upload PDF**: Use the frontend to upload a PDF document
2. **Review Pages**: View extracted pages and their character counts
3. **Test Translation**: Test translate individual pages to verify quality
4. **Start Full Translation**: Begin processing all pages with Celery workers
5. **Monitor Progress**: Use Flower dashboard to monitor translation progress

## Database Schema

### PDFDocument
- Document metadata, file paths, status tracking
- Total pages and character counts

### PDFPage
- Individual page content and translation status
- Translation metadata (model, time, cost estimates)
- Test page flagging

### TranslationJob
- Celery task tracking and progress monitoring
- Cost estimation and completion tracking

## Configuration

### Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `OPENAI_API_KEY`: OpenAI API key for translations
- `OPENAI_MODEL`: GPT model to use (default: gpt-3.5-turbo-instruct)
- `UPLOAD_DIR`: Directory for storing uploaded files
- `MAX_FILE_SIZE`: Maximum file size in bytes

### Docker Services

- **postgres**: PostgreSQL 13 database
- **redis**: Redis 7 message broker
- **backend**: FastAPI application
- **celery-worker**: Background translation workers
- **flower**: Celery monitoring dashboard

## Production Considerations

- Set up proper logging and monitoring
- Configure SSL/TLS for production
- Set up database backups
- Monitor OpenAI API usage and costs
- Scale Celery workers based on load
- Implement rate limiting for API endpoints
- Set up proper error alerting

## Cost Estimation

The system provides cost estimation for translations based on:
- Character count in source text
- GPT-3.5 Turbo pricing ($1.50 per 1M tokens)
- Approximate 4 characters per token ratio

## Troubleshooting

### Common Issues

1. **Database Connection**: Ensure PostgreSQL is running and accessible
2. **Redis Connection**: Check Redis service status
3. **OpenAI API**: Verify API key and rate limits
4. **File Uploads**: Check upload directory permissions
5. **Celery Workers**: Monitor worker logs for task failures

### Logs

```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f celery-worker
```

## License

This project is open source and available under the MIT License.
