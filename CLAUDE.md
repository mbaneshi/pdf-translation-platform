# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Commands

### Backend Development
```bash
cd backend
python -m uvicorn app.main:app --reload    # Start development server
python -m pytest tests/ -v                 # Run tests
python -m black app/ tests/                # Format code
python -m isort app/ tests/                # Sort imports
python -m ruff check app/ tests/           # Lint code
python -m mypy app/ --ignore-missing-imports # Type check
alembic upgrade head                        # Run database migrations
celery -A app.workers.celery_worker.celery_app worker --loglevel=info # Start Celery worker
```

### Frontend Development
```bash
cd frontend
npm run dev                                 # Start development server
npm run build                              # Build for production
npm run lint                               # Lint code
npm test                                   # Run tests
npm run test:coverage                      # Run tests with coverage
npx tsc --noEmit                          # Type check
```

### Full Quality Check
```bash
./check-quality.sh                        # Run all quality checks (backend and frontend)
```

### Docker Development
```bash
docker-compose up -d postgres redis       # Start infrastructure
docker-compose up -d backend celery-worker flower # Start application services
docker-compose logs -f                    # View logs
```

## Architecture Overview

This is a comprehensive PDF translation platform that translates English documents (particularly academic/philosophical texts) to Persian using OpenAI's GPT models. The system features:

**Core Stack:**
- **Backend:** FastAPI with Python 3.11, PostgreSQL database, Redis for caching/messaging
- **Frontend:** Next.js with TypeScript, Tailwind CSS, Pages Router architecture
- **Processing:** Celery workers for async translation, PyMuPDF for PDF processing
- **External:** OpenAI API for translation, Traefik for reverse proxy

**Key Architecture Components:**

### Backend Structure (`backend/app/`)
- **`main.py`**: FastAPI application entry point with CORS and router configuration
- **`models/models.py`**: Enhanced SQLAlchemy models with semantic analysis support:
  - `PDFDocument`: Document metadata with complexity scoring and cost estimates
  - `PDFPage`: Page-level content with semantic structures and format preservation
  - `SemanticStructure`: Sentence/paragraph/section level translation units
  - `TranslationJob`: Celery task tracking with progress monitoring
  - `SampleTranslation`: Quality assessment and user feedback
  - `FormatPreservation`: Layout and formatting preservation data
- **`api/endpoints/`**: API routes with enhanced document processing capabilities
- **`services/semantic_analyzer.py`**: Document analysis and chunking strategies
- **`workers/celery_worker.py`**: Background task processing
- **`core/`**: Configuration, database setup, and utilities

### Frontend Structure (`frontend/`)
- **`pages/`**: Next.js pages using Pages Router (not App Router)
  - `index.js`: Main document upload and management interface
  - `_app.js`: Application wrapper
- **`components/`**: Reusable React components for document viewer and translation UI
- **`contexts/`**: React context for state management
- **`lib/`**: API client and utility functions
- **`types/`**: TypeScript type definitions

### Processing Pipeline
1. **Document Upload**: PDF processing with PyMuPDF, metadata extraction
2. **Semantic Analysis**: Document structure analysis, complexity scoring, chunking strategy recommendation
3. **Sample Translation**: Test page translation for quality validation
4. **Full Translation**: Async processing with Celery, semantic-aware chunking
5. **Quality Assurance**: Persian text processing, format preservation, cost tracking

### Database Schema
The system uses enhanced models supporting:
- Document-level analysis and metadata
- Page-level semantic structures (sentences, paragraphs, sections)
- Translation job tracking with progress monitoring
- Quality reports and user feedback
- Format preservation data for layout maintenance

## Development Guidelines

### Code Style
- **Backend**: Uses Black (88 char limit), isort, Ruff, and MyPy configured in `pyproject.toml`
- **Frontend**: Uses ESLint with Next.js config, TypeScript strict mode
- **Pre-commit hooks**: Automated formatting and linting via `.pre-commit-config.yaml`

### Testing
- **Backend**: pytest with fixtures for database and integration tests
- **Frontend**: Jest with React Testing Library, coverage thresholds at 80%
- **Quality checks**: Use `./check-quality.sh` before committing

### API Design
- RESTful endpoints under `/api/` prefix
- Enhanced endpoints for semantic analysis (`/api/enhanced/`)
- Comprehensive error handling with proper HTTP status codes
- OpenAPI documentation available at `/docs`

### Environment Configuration
Key environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection for Celery and caching
- `OPENAI_API_KEY`: Required for translation functionality
- `ENVIRONMENT`: Development/production mode switching

### Deployment
- Production deployment uses Traefik reverse proxy with SSL
- Docker Compose with health checks and auto-restart
- Separate services for API, frontend, workers, and monitoring (Flower)
- Database backups and logging configured

## Important Notes

- The system is designed for **academic/philosophical content translation** with Persian language optimization
- **Cost estimation** is critical - all translation operations include cost tracking and validation
- **Quality assurance** is built-in with sample translation testing before full processing
- **Semantic analysis** drives the chunking strategy for optimal translation quality
- **Format preservation** maintains document layout and styling in Persian output
- The frontend uses **Pages Router** (not App Router) - follow existing patterns
- **Security**: Never commit API keys, use environment variables for all secrets
- **Performance**: Leverage Redis caching for repeated translations and document analysis results