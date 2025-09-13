# Enhanced Database Models for Semantic PDF Translation
# backend/app/models/enhanced_models.py

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, Float, BigInteger, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class PDFDocument(Base):
    __tablename__ = "pdf_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    
    # Document metrics
    total_pages = Column(Integer, default=0)
    total_characters = Column(Integer, default=0)
    file_size_bytes = Column(BigInteger, default=0)
    
    # Document analysis
    text_density_score = Column(Float, default=0.0)
    layout_complexity_score = Column(Float, default=0.0)
    academic_term_count = Column(Integer, default=0)
    philosophical_concept_count = Column(Integer, default=0)
    proper_noun_count = Column(Integer, default=0)
    language_complexity_score = Column(Float, default=0.0)
    
    # Translation estimates
    total_tokens = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0.0)
    recommended_chunking_strategy = Column(String(50), default='semantic')
    persian_expansion_factor = Column(Float, default=1.2)
    
    # Processing recommendations
    processing_priority = Column(String(20), default='medium')
    quality_requirements = Column(String(20), default='standard')
    estimated_processing_time_minutes = Column(Integer, default=0)
    
    # Status and metadata
    status = Column(String(50), default="uploaded")
    document_metadata = Column(JSON, default=dict)
    analysis_completed = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pages = relationship("PDFPage", back_populates="document", cascade="all, delete-orphan")
    translation_jobs = relationship("TranslationJob", back_populates="document", cascade="all, delete-orphan")
    sample_translations = relationship("SampleTranslation", back_populates="document", cascade="all, delete-orphan")

class PDFPage(Base):
    __tablename__ = "pdf_pages"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("pdf_documents.id"), index=True)
    page_number = Column(Integer, nullable=False)
    
    # Original content
    original_text = Column(Text)
    char_count = Column(Integer, default=0)
    word_count = Column(Integer, default=0)
    sentence_count = Column(Integer, default=0)
    paragraph_count = Column(Integer, default=0)
    
    # Semantic structure
    sentences = Column(JSON, default=list)  # Array of sentence objects
    paragraphs = Column(JSON, default=list)  # Array of paragraph objects
    sections = Column(JSON, default=list)   # Array of section objects
    chapters = Column(JSON, default=list)   # Array of chapter objects
    
    # Content analysis
    academic_terms = Column(JSON, default=list)
    philosophical_concepts = Column(JSON, default=list)
    proper_nouns = Column(JSON, default=list)
    technical_terms = Column(JSON, default=list)
    
    # Complexity metrics
    readability_score = Column(Float, default=0.0)
    complexity_score = Column(Float, default=0.0)
    translation_difficulty = Column(String(20), default='medium')
    
    # Translation estimates
    estimated_tokens = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0.0)
    estimated_translation_time_seconds = Column(Integer, default=0)
    
    # Recommendations
    recommended_chunk_size = Column(Integer, default=1000)
    requires_special_handling = Column(Boolean, default=False)
    quality_priority = Column(String(20), default='medium')
    
    # Translation results
    translated_text = Column(Text)
    translation_status = Column(String(50), default="pending")
    translation_model = Column(String(100))
    translation_time = Column(Float)
    cost_estimate = Column(Float, default=0.0)
    is_test_page = Column(Boolean, default=False)
    
    # Format preservation
    original_layout = Column(JSON, default=dict)  # Layout information
    preserved_formatting = Column(JSON, default=dict)  # Formatting preservation data
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    document = relationship("PDFDocument", back_populates="pages")
    semantic_structures = relationship("SemanticStructure", back_populates="page", cascade="all, delete-orphan", primaryjoin="PDFPage.id == SemanticStructure.page_id")
    sample_translations = relationship("SampleTranslation", back_populates="page", cascade="all, delete-orphan")
    format_preservation = relationship("FormatPreservation", back_populates="page", cascade="all, delete-orphan")

class SemanticStructure(Base):
    __tablename__ = "semantic_structures"
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pdf_pages.id"), index=True)
    structure_type = Column(String(50), nullable=False)  # sentence, paragraph, section, chapter
    structure_index = Column(Integer, nullable=False)     # Order within the page
    
    # Content
    original_text = Column(Text, nullable=False)
    translated_text = Column(Text)
    
    # Metadata
    char_count = Column(Integer, default=0)
    word_count = Column(Integer, default=0)
    complexity_score = Column(Float, default=0.0)
    
    # Translation status
    translation_status = Column(String(50), default="pending")
    translation_cost = Column(Float, default=0.0)
    translation_time = Column(Float, default=0.0)
    
    # Format preservation
    formatting_data = Column(JSON, default=dict)
    layout_position = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    page = relationship("PDFPage", back_populates="semantic_structures")

class TranslationJob(Base):
    __tablename__ = "translation_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("pdf_documents.id"), index=True)
    celery_task_id = Column(String(255), unique=True)
    
    # Job details
    job_type = Column(String(50), default='full_translation')  # full, sample, gradual
    status = Column(String(50), default="pending")
    
    # Progress tracking
    pages_processed = Column(Integer, default=0)
    total_pages = Column(Integer, default=0)
    structures_processed = Column(Integer, default=0)
    total_structures = Column(Integer, default=0)
    
    # Cost tracking
    estimated_cost = Column(Float, default=0.0)
    actual_cost = Column(Float, default=0.0)
    
    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Results
    results_summary = Column(JSON, default=dict)
    error_log = Column(JSON, default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("PDFDocument", back_populates="translation_jobs")

class SampleTranslation(Base):
    __tablename__ = "sample_translations"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("pdf_documents.id"), index=True)
    page_id = Column(Integer, ForeignKey("pdf_pages.id"), index=True)
    
    # Sample details
    sample_type = Column(String(50), default='page')  # page, paragraph, sentence
    sample_text = Column(Text, nullable=False)
    translated_text = Column(Text)
    
    # Analysis
    quality_score = Column(Float, default=0.0)
    cost_estimate = Column(Float, default=0.0)
    processing_time = Column(Float, default=0.0)
    
    # User feedback
    user_approved = Column(Boolean, default=False)
    user_feedback = Column(Text)
    adjustments_made = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("PDFDocument", back_populates="sample_translations")
    page = relationship("PDFPage", back_populates="sample_translations")

class FormatPreservation(Base):
    __tablename__ = "format_preservation"
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pdf_pages.id"), index=True)
    
    # Layout information
    layout_type = Column(String(50), default='text')  # text, table, column, image
    layout_data = Column(JSON, default=dict)
    
    # Original formatting
    fonts = Column(JSON, default=list)
    colors = Column(JSON, default=list)
    spacing = Column(JSON, default=dict)
    
    # Preservation status
    preserved = Column(Boolean, default=False)
    preservation_method = Column(String(50))
    preservation_data = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    page = relationship("PDFPage", back_populates="format_preservation")
