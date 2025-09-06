from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class PDFDocument(Base):
    __tablename__ = "pdf_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    total_pages = Column(Integer, default=0)
    total_characters = Column(Integer, default=0)
    status = Column(String(50), default="uploaded")  # uploaded, processing, completed, failed
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PDFPage(Base):
    __tablename__ = "pdf_pages"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, index=True)
    page_number = Column(Integer, nullable=False)
    original_text = Column(Text)
    translated_text = Column(Text)
    char_count = Column(Integer, default=0)
    translation_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    translation_model = Column(String(100))
    translation_time = Column(Float)  # seconds
    cost_estimate = Column(Float, default=0.0)
    is_test_page = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TranslationJob(Base):
    __tablename__ = "translation_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, index=True)
    celery_task_id = Column(String(255), unique=True)
    status = Column(String(50), default="pending")
    pages_processed = Column(Integer, default=0)
    total_pages = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    actual_cost = Column(Float, default=0.0)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
