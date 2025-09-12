# Semantic Analysis Engine for PDF Translation
# backend/app/services/semantic_analyzer.py

import fitz
import re
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class StructureType(Enum):
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    SECTION = "section"
    CHAPTER = "chapter"
    TABLE = "table"
    COLUMN = "column"

@dataclass
class SemanticStructure:
    type: StructureType
    index: int
    text: str
    char_count: int
    word_count: int
    complexity_score: float
    formatting_data: Dict = None
    layout_position: Dict = None

@dataclass
class LayoutInfo:
    layout_type: str
    column_count: int
    table_data: List[Dict]
    formatting: Dict
    spacing: Dict

class SemanticAnalyzer:
    def __init__(self):
        self.academic_terms = self._load_academic_terms()
        self.philosophical_concepts = self._load_philosophical_concepts()
        self.proper_nouns = self._load_proper_nouns()
        
    def analyze_document_structure(self, file_path: str) -> Dict:
        """Extract comprehensive semantic structure from PDF"""
        try:
            doc = fitz.open(file_path)
            document_structures = {
                "sentences": [],
                "paragraphs": [],
                "sections": [],
                "chapters": [],
                "tables": [],
                "columns": []
            }
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                page_structures = self._analyze_page_structure(page, page_num)
                
                # Aggregate structures by type
                for structure_type, structures in page_structures.items():
                    document_structures[structure_type].extend(structures)
            
            doc.close()
            return document_structures
            
        except Exception as e:
            logger.error(f"Error analyzing document structure: {e}")
            raise
    
    def analyze_page_structure(self, page, page_number: int) -> Dict:
        """Analyze semantic structure of a single page"""
        try:
            # Extract text and layout information
            text = page.get_text()
            layout_info = self._extract_layout_info(page)
            
            # Extract semantic structures
            sentences = self._extract_sentences(text, page_number)
            paragraphs = self._extract_paragraphs(text, page_number)
            sections = self._extract_sections(text, page_number)
            chapters = self._extract_chapters(text, page_number)
            tables = self._extract_tables(page, page_number)
            columns = self._extract_columns(page, page_number)
            
            return {
                "sentences": sentences,
                "paragraphs": paragraphs,
                "sections": sections,
                "chapters": chapters,
                "tables": tables,
                "columns": columns
            }
            
        except Exception as e:
            logger.error(f"Error analyzing page {page_number}: {e}")
            raise
    
    def _extract_sentences(self, text: str, page_number: int) -> List[Dict]:
        """Extract sentences from text"""
        sentences = []
        
        # Split text into sentences using regex
        sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])'
        sentence_texts = re.split(sentence_pattern, text)
        
        for i, sentence_text in enumerate(sentence_texts):
            if sentence_text.strip():
                sentence = SemanticStructure(
                    type=StructureType.SENTENCE,
                    index=i,
                    text=sentence_text.strip(),
                    char_count=len(sentence_text),
                    word_count=len(sentence_text.split()),
                    complexity_score=self._calculate_complexity_score(sentence_text)
                )
                sentences.append({
                    "type": sentence.type.value,
                    "index": sentence.index,
                    "text": sentence.text,
                    "char_count": sentence.char_count,
                    "word_count": sentence.word_count,
                    "complexity_score": sentence.complexity_score,
                    "page_number": page_number
                })
        
        return sentences
    
    def _extract_paragraphs(self, text: str, page_number: int) -> List[Dict]:
        """Extract paragraphs from text"""
        paragraphs = []
        
        # Split text into paragraphs
        paragraph_texts = text.split('\n\n')
        
        for i, paragraph_text in enumerate(paragraph_texts):
            if paragraph_text.strip():
                paragraph = SemanticStructure(
                    type=StructureType.PARAGRAPH,
                    index=i,
                    text=paragraph_text.strip(),
                    char_count=len(paragraph_text),
                    word_count=len(paragraph_text.split()),
                    complexity_score=self._calculate_complexity_score(paragraph_text)
                )
                paragraphs.append({
                    "type": paragraph.type.value,
                    "index": paragraph.index,
                    "text": paragraph.text,
                    "char_count": paragraph.char_count,
                    "word_count": paragraph.word_count,
                    "complexity_score": paragraph.complexity_score,
                    "page_number": page_number
                })
        
        return paragraphs
    
    def _extract_sections(self, text: str, page_number: int) -> List[Dict]:
        """Extract sections from text"""
        sections = []
        
        # Look for section headers (numbered sections, headings)
        section_pattern = r'(?:^|\n)\s*(?:\d+\.?\s+)?[A-Z][A-Z\s]+(?:\n|$)'
        section_matches = re.finditer(section_pattern, text, re.MULTILINE)
        
        for i, match in enumerate(section_matches):
            section_text = match.group().strip()
            sections.append({
                "type": StructureType.SECTION.value,
                "index": i,
                "text": section_text,
                "char_count": len(section_text),
                "word_count": len(section_text.split()),
                "complexity_score": self._calculate_complexity_score(section_text),
                "page_number": page_number
            })
        
        return sections
    
    def _extract_chapters(self, text: str, page_number: int) -> List[Dict]:
        """Extract chapters from text"""
        chapters = []
        
        # Look for chapter headers
        chapter_pattern = r'(?:^|\n)\s*(?:Chapter\s+\d+|CHAPTER\s+\d+)[:\s]*(.+?)(?:\n|$)'
        chapter_matches = re.finditer(chapter_pattern, text, re.MULTILINE | re.IGNORECASE)
        
        for i, match in enumerate(chapter_matches):
            chapter_text = match.group().strip()
            chapters.append({
                "type": StructureType.CHAPTER.value,
                "index": i,
                "text": chapter_text,
                "char_count": len(chapter_text),
                "word_count": len(chapter_text.split()),
                "complexity_score": self._calculate_complexity_score(chapter_text),
                "page_number": page_number
            })
        
        return chapters
    
    def _extract_tables(self, page, page_number: int) -> List[Dict]:
        """Extract tables from page"""
        tables = []
        
        try:
            # Look for table-like structures in text
            text = page.get_text()
            
            # Simple table detection based on patterns
            table_pattern = r'(?:^|\n)(?:\s*\w+\s*\|.*\|.*\n)+'
            table_matches = re.finditer(table_pattern, text, re.MULTILINE)
            
            for i, match in enumerate(table_matches):
                table_text = match.group().strip()
                tables.append({
                    "type": StructureType.TABLE.value,
                    "index": i,
                    "text": table_text,
                    "char_count": len(table_text),
                    "word_count": len(table_text.split()),
                    "complexity_score": self._calculate_complexity_score(table_text),
                    "page_number": page_number,
                    "table_data": self._parse_table_data(table_text)
                })
        
        except Exception as e:
            logger.warning(f"Error extracting tables from page {page_number}: {e}")
        
        return tables
    
    def _extract_columns(self, page, page_number: int) -> List[Dict]:
        """Extract column information from page"""
        columns = []
        
        try:
            # Analyze page layout for columns
            layout_info = self._extract_layout_info(page)
            
            if layout_info.column_count > 1:
                columns.append({
                    "type": StructureType.COLUMN.value,
                    "index": 0,
                    "text": f"Multi-column layout detected ({layout_info.column_count} columns)",
                    "char_count": 0,
                    "word_count": 0,
                    "complexity_score": 0.5,
                    "page_number": page_number,
                    "column_count": layout_info.column_count,
                    "layout_data": layout_info.layout_data
                })
        
        except Exception as e:
            logger.warning(f"Error extracting columns from page {page_number}: {e}")
        
        return columns
    
    def _extract_layout_info(self, page) -> LayoutInfo:
        """Extract layout information from page"""
        try:
            # Get page dimensions
            rect = page.rect
            
            # Analyze text blocks for layout
            blocks = page.get_text("dict")
            
            # Simple column detection
            column_count = self._detect_columns(blocks)
            
            # Extract formatting information
            formatting = self._extract_formatting_info(blocks)
            
            return LayoutInfo(
                layout_type="text" if column_count == 1 else "multi-column",
                column_count=column_count,
                table_data=[],
                formatting=formatting,
                spacing={}
            )
            
        except Exception as e:
            logger.warning(f"Error extracting layout info: {e}")
            return LayoutInfo(
                layout_type="text",
                column_count=1,
                table_data=[],
                formatting={},
                spacing={}
            )
    
    def _detect_columns(self, blocks: List[Dict]) -> int:
        """Detect number of columns in text blocks"""
        try:
            if not blocks or 'blocks' not in blocks:
                return 1
            
            # Analyze block positions to detect columns
            x_positions = []
            for block in blocks['blocks']:
                if 'bbox' in block:
                    x_positions.append(block['bbox'][0])
            
            if not x_positions:
                return 1
            
            # Group x-positions to detect columns
            x_positions.sort()
            columns = 1
            threshold = 50  # pixels
            
            for i in range(1, len(x_positions)):
                if x_positions[i] - x_positions[i-1] > threshold:
                    columns += 1
            
            return min(columns, 3)  # Cap at 3 columns
            
        except Exception as e:
            logger.warning(f"Error detecting columns: {e}")
            return 1
    
    def _extract_formatting_info(self, blocks: List[Dict]) -> Dict:
        """Extract formatting information from blocks"""
        try:
            formatting = {
                "fonts": set(),
                "sizes": set(),
                "colors": set()
            }
            
            if not blocks or 'blocks' not in blocks:
                return formatting
            
            for block in blocks['blocks']:
                if 'lines' in block:
                    for line in block['lines']:
                        if 'spans' in line:
                            for span in line['spans']:
                                if 'font' in span:
                                    formatting["fonts"].add(span['font'])
                                if 'size' in span:
                                    formatting["sizes"].add(span['size'])
                                if 'color' in span:
                                    formatting["colors"].add(span['color'])
            
            # Convert sets to lists for JSON serialization
            formatting["fonts"] = list(formatting["fonts"])
            formatting["sizes"] = list(formatting["sizes"])
            formatting["colors"] = list(formatting["colors"])
            
            return formatting
            
        except Exception as e:
            logger.warning(f"Error extracting formatting info: {e}")
            return {"fonts": [], "sizes": [], "colors": []}
    
    def _parse_table_data(self, table_text: str) -> List[Dict]:
        """Parse table data from text"""
        try:
            rows = table_text.strip().split('\n')
            table_data = []
            
            for row in rows:
                if '|' in row:
                    cells = [cell.strip() for cell in row.split('|')]
                    table_data.append({
                        "cells": cells,
                        "cell_count": len(cells)
                    })
            
            return table_data
            
        except Exception as e:
            logger.warning(f"Error parsing table data: {e}")
            return []
    
    def _calculate_complexity_score(self, text: str) -> float:
        """Calculate complexity score for text (0-1)"""
        try:
            if not text:
                return 0.0
            
            # Factors for complexity
            word_count = len(text.split())
            sentence_count = len(re.findall(r'[.!?]+', text))
            avg_words_per_sentence = word_count / max(sentence_count, 1)
            
            # Academic term density
            academic_term_count = sum(1 for term in self.academic_terms if term.lower() in text.lower())
            academic_density = academic_term_count / max(word_count, 1)
            
            # Philosophical concept density
            philosophical_count = sum(1 for concept in self.philosophical_concepts if concept.lower() in text.lower())
            philosophical_density = philosophical_count / max(word_count, 1)
            
            # Calculate complexity score
            complexity = (
                min(avg_words_per_sentence / 20, 1.0) * 0.3 +  # Sentence length factor
                min(academic_density * 10, 1.0) * 0.4 +        # Academic term factor
                min(philosophical_density * 10, 1.0) * 0.3     # Philosophical concept factor
            )
            
            return min(complexity, 1.0)
            
        except Exception as e:
            logger.warning(f"Error calculating complexity score: {e}")
            return 0.5
    
    def _load_academic_terms(self) -> List[str]:
        """Load academic terminology list"""
        return [
            "analysis", "theory", "concept", "philosophy", "methodology",
            "framework", "paradigm", "discourse", "phenomenology", "ontology",
            "epistemology", "hermeneutics", "dialectics", "metaphysics",
            "existentialism", "phenomenology", "hermeneutics", "deconstruction"
        ]
    
    def _load_philosophical_concepts(self) -> List[str]:
        """Load philosophical concepts list"""
        return [
            "being", "existence", "authenticity", "truth", "reality",
            "consciousness", "subjectivity", "objectivity", "meaning",
            "interpretation", "understanding", "experience", "perception",
            "knowledge", "wisdom", "enlightenment", "transcendence"
        ]
    
    def _load_proper_nouns(self) -> List[str]:
        """Load proper nouns list"""
        return [
            "Werner Erhard", "Martin Heidegger", "Jean-Paul Sartre",
            "Friedrich Nietzsche", "Immanuel Kant", "Plato", "Aristotle"
        ]
