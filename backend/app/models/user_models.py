# User Authentication Models
# backend/app/models/user_models.py

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    """User model for authentication and user management"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    
    # User status and verification
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)
    
    # Password reset
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    
    # User preferences
    language_preference = Column(String(10), default="en")
    timezone = Column(String(50), default="UTC")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    documents = relationship("PDFDocument", back_populates="user")
    glossary_entries = relationship("Glossary", back_populates="user")
    prompt_templates = relationship("PromptTemplate", back_populates="user")
    # translation_jobs relationship moved to app.models.models
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', full_name='{self.full_name}')>"

class Glossary(Base):
    """Glossary model for user-specific terminology"""
    __tablename__ = "glossary"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Term information
    term = Column(String(255), nullable=False)
    translation = Column(String(255), nullable=False)
    context = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)
    
    # Quality metrics
    confidence_score = Column(Float, default=1.0)
    user_rating = Column(Integer, nullable=True)  # 1-5 rating
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="glossary_entries")
    
    def __repr__(self):
        return f"<Glossary(id={self.id}, term='{self.term}', translation='{self.translation}')>"

class PromptTemplate(Base):
    """Prompt template model for user-specific translation prompts"""
    __tablename__ = "prompt_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Template information
    name = Column(String(255), nullable=False)
    template = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    
    # Template settings
    is_default = Column(Boolean, default=False)
    is_public = Column(Boolean, default=False)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)
    
    # Quality metrics
    success_rate = Column(Float, default=0.0)
    average_quality_score = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="prompt_templates")
    # translation_jobs relationship moved to app.models.models
    
    def __repr__(self):
        return f"<PromptTemplate(id={self.id}, name='{self.name}', category='{self.category}')>"

# TranslationJob model moved to app.models.models to avoid duplication
# Import it from there: from app.models.models import TranslationJob

class UserSession(Base):
    """User session model for session management"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Session information
    session_token = Column(String(255), unique=True, nullable=False)
    refresh_token = Column(String(255), unique=True, nullable=True)
    
    # Session metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_info = Column(String(255), nullable=True)
    
    # Session status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"

class UserActivity(Base):
    """User activity log for audit and analytics"""
    __tablename__ = "user_activities"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, default=generate_uuid, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Activity information
    activity_type = Column(String(100), nullable=False)  # login, logout, upload, translate, etc.
    activity_description = Column(Text, nullable=True)
    
    # Activity metadata
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    additional_data = Column(Text, nullable=True)  # JSON string
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<UserActivity(id={self.id}, user_id={self.user_id}, type='{self.activity_type}')>"
