# Import all models from models.py
from app.models.models import (
    PDFDocument,
    PDFPage, 
    TranslationJob,
    SemanticStructure,
    SampleTranslation,
    FormatPreservation,
    generate_uuid
)

# Re-export for backward compatibility
__all__ = [
    'PDFDocument',
    'PDFPage',
    'TranslationJob', 
    'SemanticStructure',
    'SampleTranslation',
    'FormatPreservation',
    'generate_uuid'
]
