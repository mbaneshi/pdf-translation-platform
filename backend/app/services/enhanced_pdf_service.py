# Enhanced PDF Processing Service with Layout Preservation
# backend/app/services/enhanced_pdf_service.py

import fitz
import pdfplumber
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging
from sqlalchemy.orm import Session
from app.models import PDFDocument, PDFPage
from app.core.config import settings

logger = logging.getLogger(__name__)

@dataclass
class LayoutElement:
    """Represents a layout element in the PDF"""
    element_type: str  # text, table, image, header, footer
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)
    text: str
    font_info: Dict
    formatting: Dict

@dataclass
class TableStructure:
    """Represents table structure"""
    rows: List[List[str]]
    columns: int
    bbox: Tuple[float, float, float, float]
    headers: List[str]

class EnhancedPDFService:
    """Enhanced PDF processing with layout preservation"""
    
    def __init__(self):
        self.fitz = fitz
        self.pdfplumber = pdfplumber
        
    def extract_with_layout_preservation(self, file_path: str) -> Dict:
        """Extract PDF content with full layout preservation"""
        try:
            # Use PyMuPDF for basic extraction
            basic_content = self._extract_basic_content(file_path)
            
            # Use pdfplumber for detailed layout analysis
            layout_content = self._extract_layout_content(file_path)
            
            # Combine and analyze
            combined_content = self._combine_content(basic_content, layout_content)
            
            return combined_content
            
        except Exception as e:
            logger.error(f"Error extracting PDF with layout preservation: {e}")
            raise
    
    def _extract_basic_content(self, file_path: str) -> Dict:
        """Extract basic content using PyMuPDF"""
        try:
            doc = fitz.open(file_path)
            pages_data = []
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Extract text
                text = page.get_text()
                
                # Extract text blocks with positioning
                blocks = page.get_text("dict")
                
                # Extract images
                images = page.get_images()
                
                page_data = {
                    'page_number': page_num + 1,
                    'text': text,
                    'blocks': blocks,
                    'images': images,
                    'dimensions': page.rect
                }
                
                pages_data.append(page_data)
            
            doc.close()
            return {'pages': pages_data}
            
        except Exception as e:
            logger.error(f"Error in basic content extraction: {e}")
            raise
    
    def _extract_layout_content(self, file_path: str) -> Dict:
        """Extract detailed layout using pdfplumber"""
        try:
            with pdfplumber.open(file_path) as pdf:
                pages_data = []
                
                for page_num, page in enumerate(pdf.pages):
                    # Extract text with positioning
                    text_objects = page.chars
                    
                    # Extract tables
                    tables = page.extract_tables()
                    
                    # Extract layout information
                    layout = self._analyze_page_layout(page)
                    
                    page_data = {
                        'page_number': page_num + 1,
                        'text_objects': text_objects,
                        'tables': tables,
                        'layout': layout,
                        'dimensions': (page.width, page.height)
                    }
                    
                    pages_data.append(page_data)
                
                return {'pages': pages_data}
                
        except Exception as e:
            logger.error(f"Error in layout content extraction: {e}")
            raise
    
    def _analyze_page_layout(self, page) -> Dict:
        """Analyze page layout structure"""
        try:
            layout_info = {
                'columns': self._detect_columns(page),
                'headers': self._detect_headers(page),
                'footers': self._detect_footers(page),
                'margins': self._detect_margins(page),
                'text_regions': self._detect_text_regions(page)
            }
            
            return layout_info
            
        except Exception as e:
            logger.warning(f"Error analyzing page layout: {e}")
            return {}
    
    def _detect_columns(self, page) -> int:
        """Detect number of columns in the page"""
        try:
            # Get text objects
            chars = page.chars
            
            if not chars:
                return 1
            
            # Group characters by x-position
            x_positions = [char['x0'] for char in chars]
            x_positions.sort()
            
            # Detect column boundaries
            columns = 1
            threshold = 50  # pixels
            
            for i in range(1, len(x_positions)):
                if x_positions[i] - x_positions[i-1] > threshold:
                    columns += 1
            
            return min(columns, 3)  # Cap at 3 columns
            
        except Exception as e:
            logger.warning(f"Error detecting columns: {e}")
            return 1
    
    def _detect_headers(self, page) -> List[Dict]:
        """Detect headers in the page"""
        try:
            headers = []
            
            # Look for text in the top 10% of the page
            page_height = page.height
            header_zone = page_height * 0.1
            
            chars = page.chars
            for char in chars:
                if char['top'] < header_zone:
                    headers.append({
                        'text': char['text'],
                        'position': (char['x0'], char['top']),
                        'font_size': char.get('size', 12)
                    })
            
            return headers
            
        except Exception as e:
            logger.warning(f"Error detecting headers: {e}")
            return []
    
    def _detect_footers(self, page) -> List[Dict]:
        """Detect footers in the page"""
        try:
            footers = []
            
            # Look for text in the bottom 10% of the page
            page_height = page.height
            footer_zone = page_height * 0.9
            
            chars = page.chars
            for char in chars:
                if char['top'] > footer_zone:
                    footers.append({
                        'text': char['text'],
                        'position': (char['x0'], char['top']),
                        'font_size': char.get('size', 12)
                    })
            
            return footers
            
        except Exception as e:
            logger.warning(f"Error detecting footers: {e}")
            return []
    
    def _detect_margins(self, page) -> Dict:
        """Detect page margins"""
        try:
            chars = page.chars
            
            if not chars:
                return {'left': 0, 'right': 0, 'top': 0, 'bottom': 0}
            
            # Find extreme positions
            left_margin = min(char['x0'] for char in chars)
            right_margin = page.width - max(char['x1'] for char in chars)
            top_margin = min(char['top'] for char in chars)
            bottom_margin = page.height - max(char['bottom'] for char in chars)
            
            return {
                'left': left_margin,
                'right': right_margin,
                'top': top_margin,
                'bottom': bottom_margin
            }
            
        except Exception as e:
            logger.warning(f"Error detecting margins: {e}")
            return {'left': 0, 'right': 0, 'top': 0, 'bottom': 0}
    
    def _detect_text_regions(self, page) -> List[Dict]:
        """Detect text regions in the page"""
        try:
            regions = []
            
            # Group characters into text regions
            chars = page.chars
            if not chars:
                return regions
            
            # Sort characters by position
            chars.sort(key=lambda c: (c['top'], c['x0']))
            
            current_region = None
            
            for char in chars:
                if current_region is None:
                    current_region = {
                        'text': char['text'],
                        'bbox': (char['x0'], char['top'], char['x1'], char['bottom']),
                        'font_size': char.get('size', 12)
                    }
                else:
                    # Check if character belongs to current region
                    if self._char_belongs_to_region(char, current_region):
                        current_region['text'] += char['text']
                        # Update bbox
                        current_region['bbox'] = (
                            min(current_region['bbox'][0], char['x0']),
                            min(current_region['bbox'][1], char['top']),
                            max(current_region['bbox'][2], char['x1']),
                            max(current_region['bbox'][3], char['bottom'])
                        )
                    else:
                        # Start new region
                        regions.append(current_region)
                        current_region = {
                            'text': char['text'],
                            'bbox': (char['x0'], char['top'], char['x1'], char['bottom']),
                            'font_size': char.get('size', 12)
                        }
            
            if current_region:
                regions.append(current_region)
            
            return regions
            
        except Exception as e:
            logger.warning(f"Error detecting text regions: {e}")
            return []
    
    def _char_belongs_to_region(self, char: Dict, region: Dict) -> bool:
        """Check if character belongs to current text region"""
        try:
            # Check vertical alignment
            char_top = char['top']
            region_top = region['bbox'][1]
            region_bottom = region['bbox'][3]
            
            # Allow some tolerance for line breaks
            tolerance = 5
            
            return region_top - tolerance <= char_top <= region_bottom + tolerance
            
        except Exception as e:
            logger.warning(f"Error checking character region: {e}")
            return False
    
    def _combine_content(self, basic_content: Dict, layout_content: Dict) -> Dict:
        """Combine basic and layout content"""
        try:
            combined_pages = []
            
            basic_pages = basic_content.get('pages', [])
            layout_pages = layout_content.get('pages', [])
            
            for i, (basic_page, layout_page) in enumerate(zip(basic_pages, layout_pages)):
                combined_page = {
                    'page_number': i + 1,
                    'text': basic_page.get('text', ''),
                    'blocks': basic_page.get('blocks', {}),
                    'images': basic_page.get('images', []),
                    'dimensions': basic_page.get('dimensions'),
                    'layout': layout_page.get('layout', {}),
                    'tables': layout_page.get('tables', []),
                    'text_objects': layout_page.get('text_objects', [])
                }
                
                combined_pages.append(combined_page)
            
            return {
                'pages': combined_pages,
                'total_pages': len(combined_pages),
                'extraction_method': 'enhanced_layout_preservation'
            }
            
        except Exception as e:
            logger.error(f"Error combining content: {e}")
            raise
    
    def extract_tables(self, file_path: str) -> List[TableStructure]:
        """Extract tables from PDF with structure preservation"""
        try:
            tables = []
            
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    
                    for table_data in page_tables:
                        if table_data and len(table_data) > 1:
                            table = TableStructure(
                                rows=table_data,
                                columns=len(table_data[0]) if table_data else 0,
                                bbox=(0, 0, page.width, page.height),  # Simplified
                                headers=table_data[0] if table_data else []
                            )
                            tables.append(table)
            
            return tables
            
        except Exception as e:
            logger.error(f"Error extracting tables: {e}")
            return []
    
    def preserve_formatting(self, original_text: str, translated_text: str, layout_info: Dict) -> str:
        """Preserve formatting in translated text"""
        try:
            # This is a simplified approach - in production, you'd want more sophisticated formatting preservation
            formatted_text = translated_text
            
            # Preserve paragraph breaks
            if '\n\n' in original_text:
                formatted_text = formatted_text.replace('\n', '\n\n')
            
            # Preserve bullet points
            if original_text.startswith('•') or original_text.startswith('-'):
                formatted_text = '• ' + formatted_text
            
            return formatted_text
            
        except Exception as e:
            logger.warning(f"Error preserving formatting: {e}")
            return translated_text
    
    def save_enhanced_pdf_to_db(self, db: Session, filename: str, original_filename: str, file_path: str) -> PDFDocument:
        """Save PDF document to database with enhanced metadata"""
        try:
            # Extract enhanced content
            enhanced_content = self.extract_with_layout_preservation(file_path)
            
            # Create document record
            pdf_doc = PDFDocument(
                filename=filename,
                original_filename=original_filename,
                file_path=file_path,
                total_pages=enhanced_content.get('total_pages', 0),
                status="uploaded",
                metadata={
                    'extraction_method': 'enhanced_layout_preservation',
                    'layout_analysis': True,
                    'table_detection': True
                }
            )
            
            db.add(pdf_doc)
            db.commit()
            db.refresh(pdf_doc)
            
            # Save pages with enhanced data
            self._save_enhanced_pages(db, pdf_doc.id, enhanced_content)
            
            return pdf_doc
            
        except Exception as e:
            logger.error(f"Error saving enhanced PDF to database: {e}")
            raise
    
    def _save_enhanced_pages(self, db: Session, document_id: int, enhanced_content: Dict):
        """Save pages with enhanced layout data"""
        try:
            pages_data = enhanced_content.get('pages', [])
            
            for page_data in pages_data:
                page = PDFPage(
                    document_id=document_id,
                    page_number=page_data['page_number'],
                    original_text=page_data.get('text', ''),
                    char_count=len(page_data.get('text', '')),
                    word_count=len(page_data.get('text', '').split()),
                    translation_status="pending",
                    metadata={
                        'layout_info': page_data.get('layout', {}),
                        'tables': page_data.get('tables', []),
                        'images': page_data.get('images', []),
                        'dimensions': page_data.get('dimensions')
                    }
                )
                
                db.add(page)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error saving enhanced pages: {e}")
            raise
