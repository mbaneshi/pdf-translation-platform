# Import all models from enhanced_models to avoid duplication
from app.models.enhanced_models import (
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
