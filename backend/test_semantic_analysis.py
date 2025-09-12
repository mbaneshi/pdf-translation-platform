# Test Script for Semantic Analysis with Target PDF
# backend/test_semantic_analysis.py

import sys
import os

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

from app.services.semantic_analyzer import SemanticAnalyzer
from app.services.enhanced_pdf_service import EnhancedPDFService
from app.services.persian_text_processor import PersianTextProcessor
from app.services.translation_service import TranslationService
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_semantic_analysis():
    """Test semantic analysis with the target PDF"""
    
    # Path to your target PDF
    pdf_path = "/home/nerd/pdf/pdf-translation-platform/Bruce_Hyde,_Drew_Kopp_Speaking_Being_Werner_Erhard,_Martin_Heidegger (1).pdf"
    
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found: {pdf_path}")
        return
    
    logger.info(f"Testing semantic analysis with: {pdf_path}")
    
    try:
        # Initialize services
        semantic_analyzer = SemanticAnalyzer()
        enhanced_pdf_service = EnhancedPDFService()
        persian_processor = PersianTextProcessor()
        
        # Test 1: Enhanced PDF Processing
        logger.info("=== Test 1: Enhanced PDF Processing ===")
        enhanced_content = enhanced_pdf_service.extract_with_layout_preservation(pdf_path)
        
        logger.info(f"Total pages extracted: {enhanced_content.get('total_pages', 0)}")
        
        # Analyze first few pages
        pages = enhanced_content.get('pages', [])
        for i, page in enumerate(pages[:3]):  # Test first 3 pages
            logger.info(f"\n--- Page {page['page_number']} ---")
            logger.info(f"Text length: {len(page.get('text', ''))}")
            logger.info(f"Layout info: {page.get('layout', {})}")
            logger.info(f"Tables found: {len(page.get('tables', []))}")
            
            # Show first 200 characters of text
            text_preview = page.get('text', '')[:200]
            logger.info(f"Text preview: {text_preview}...")
        
        # Test 2: Semantic Structure Analysis
        logger.info("\n=== Test 2: Semantic Structure Analysis ===")
        
        # Analyze document structure
        document_structures = semantic_analyzer.analyze_document_structure(pdf_path)
        
        logger.info("Document structure analysis:")
        for structure_type, structures in document_structures.items():
            logger.info(f"  {structure_type}: {len(structures)} found")
            
            # Show first few examples
            for i, structure in enumerate(structures[:2]):
                logger.info(f"    Example {i+1}: {structure.get('text', '')[:100]}...")
        
        # Test 3: Persian Text Processing
        logger.info("\n=== Test 3: Persian Text Processing ===")
        
        # Test with sample English text
        sample_text = "This is a philosophical text about existence and being."
        logger.info(f"Original text: {sample_text}")
        
        # Test Persian processing (this will be empty until we have Persian text)
        processed_text = persian_processor.process_persian_text(sample_text)
        logger.info(f"Processed text: {processed_text}")
        
        # Test 4: Translation Service (if API key is available)
        logger.info("\n=== Test 4: Translation Service ===")
        
        try:
            translation_service = TranslationService()
            
            # Test translation statistics
            stats = translation_service.get_translation_statistics(sample_text)
            logger.info(f"Translation statistics: {stats}")
            
            # Test cost estimation
            cost = translation_service.estimate_cost(sample_text)
            logger.info(f"Estimated cost: ${cost:.6f}")
            
        except Exception as e:
            logger.warning(f"Translation service test failed (likely missing API key): {e}")
        
        # Test 5: Academic Term Detection
        logger.info("\n=== Test 5: Academic Term Detection ===")
        
        # Extract academic terms from first page
        if pages:
            first_page_text = pages[0].get('text', '')
            academic_terms = semantic_analyzer._load_academic_terms()
            philosophical_concepts = semantic_analyzer._load_philosophical_concepts()
            
            found_academic = [term for term in academic_terms if term.lower() in first_page_text.lower()]
            found_philosophical = [concept for concept in philosophical_concepts if concept.lower() in first_page_text.lower()]
            
            logger.info(f"Academic terms found: {found_academic}")
            logger.info(f"Philosophical concepts found: {found_philosophical}")
        
        logger.info("\n=== Semantic Analysis Test Complete ===")
        logger.info("All tests completed successfully!")
        
        return {
            'status': 'success',
            'pages_analyzed': len(pages),
            'structures_found': {k: len(v) for k, v in document_structures.items()},
            'enhanced_features': ['layout_analysis', 'semantic_structure', 'academic_term_detection']
        }
        
    except Exception as e:
        logger.error(f"Semantic analysis test failed: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }

def test_sample_translation():
    """Test sample translation functionality"""
    
    logger.info("\n=== Sample Translation Test ===")
    
    try:
        translation_service = TranslationService()
        
        # Test with sample philosophical text
        sample_texts = [
            "Existence precedes essence.",
            "Being and Time is a fundamental work of existential philosophy.",
            "The question of being is the most fundamental question in philosophy."
        ]
        
        for i, text in enumerate(sample_texts):
            logger.info(f"\nSample {i+1}: {text}")
            
            # Get translation statistics
            stats = translation_service.get_translation_statistics(text)
            logger.info(f"Stats: {stats}")
            
            # Estimate cost
            cost = translation_service.estimate_cost(text)
            logger.info(f"Estimated cost: ${cost:.6f}")
        
        logger.info("Sample translation test completed!")
        
    except Exception as e:
        logger.warning(f"Sample translation test failed: {e}")

if __name__ == "__main__":
    print("Starting Semantic Analysis Test...")
    
    # Run semantic analysis test
    result = test_semantic_analysis()
    
    # Run sample translation test
    test_sample_translation()
    
    print(f"\nTest Results: {result}")
