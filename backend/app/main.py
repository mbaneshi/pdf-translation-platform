from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.api.endpoints import documents, enhanced_documents
from app.api.endpoints import pages as pages_endpoints
from app.api.endpoints import monitoring, auth, glossary
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown
    pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://pdf.edcopo.info",  # Production frontend
        "https://apipdf.edcopo.info"  # API domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(glossary.router, prefix="/api/glossary", tags=["glossary"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"])
app.include_router(enhanced_documents.router, prefix="/api/enhanced", tags=["enhanced"])
app.include_router(pages_endpoints.router, prefix="/api/pages", tags=["pages"])
app.include_router(monitoring.router, prefix="/api/monitoring", tags=["monitoring"])

@app.get("/")
async def root():
    return {"message": "PDF Translation Platform API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/metrics")
async def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
