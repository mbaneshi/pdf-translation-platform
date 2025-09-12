# Persian Text Processor for RTL and Arabic Script Handling
# backend/app/services/persian_text_processor.py

import bidi.algorithm as bidi
import arabic_reshaper
import re
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class PersianTextProcessor:
    """Handles Persian text processing including RTL and Arabic script shaping"""
    
    def __init__(self):
        self.reshaper = arabic_reshaper.ArabicReshaper()
        self.persian_patterns = self._load_persian_patterns()
        self.academic_terms = self._load_academic_persian_terms()
        
    def process_persian_text(self, text: str) -> str:
        """Process Persian text with proper shaping and RTL handling"""
        try:
            if not text or not self._contains_persian(text):
                return text
            
            # Apply Arabic reshaping for proper character connection
            reshaped_text = self.reshaper.reshape(text)
            
            # Apply bidirectional algorithm for RTL handling
            bidi_text = bidi.get_display(reshaped_text)
            
            return bidi_text
            
        except Exception as e:
            logger.error(f"Error processing Persian text: {e}")
            return text
    
    def _contains_persian(self, text: str) -> bool:
        """Check if text contains Persian/Arabic characters"""
        persian_range = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')
        return bool(persian_range.search(text))
    
    def format_persian_text(self, text: str, preserve_spacing: bool = True) -> str:
        """Format Persian text with proper spacing and punctuation"""
        try:
            # Process the text
            processed_text = self.process_persian_text(text)
            
            if preserve_spacing:
                # Preserve original spacing patterns
                processed_text = self._preserve_spacing_patterns(text, processed_text)
            
            # Fix Persian punctuation
            processed_text = self._fix_persian_punctuation(processed_text)
            
            return processed_text
            
        except Exception as e:
            logger.error(f"Error formatting Persian text: {e}")
            return text
    
    def _preserve_spacing_patterns(self, original: str, processed: str) -> str:
        """Preserve original spacing patterns in processed text"""
        try:
            # This is a simplified approach - in production, you'd want more sophisticated spacing preservation
            return processed
        except Exception as e:
            logger.warning(f"Error preserving spacing patterns: {e}")
            return processed
    
    def _fix_persian_punctuation(self, text: str) -> str:
        """Fix Persian punctuation marks"""
        try:
            # Replace English punctuation with Persian equivalents where appropriate
            replacements = {
                '?': '؟',
                ';': '؛',
                ',': '،',
                # Add more as needed
            }
            
            for eng, per in replacements.items():
                text = text.replace(eng, per)
            
            return text
            
        except Exception as e:
            logger.warning(f"Error fixing Persian punctuation: {e}")
            return text
    
    def extract_persian_terms(self, text: str) -> List[Dict]:
        """Extract Persian terms and their contexts"""
        try:
            terms = []
            
            # Look for academic Persian terms
            for term in self.academic_terms:
                if term in text:
                    # Find context around the term
                    context = self._extract_context(text, term)
                    terms.append({
                        'term': term,
                        'context': context,
                        'type': 'academic'
                    })
            
            return terms
            
        except Exception as e:
            logger.error(f"Error extracting Persian terms: {e}")
            return []
    
    def _extract_context(self, text: str, term: str, context_length: int = 50) -> str:
        """Extract context around a term"""
        try:
            index = text.find(term)
            if index == -1:
                return ""
            
            start = max(0, index - context_length)
            end = min(len(text), index + len(term) + context_length)
            
            return text[start:end]
            
        except Exception as e:
            logger.warning(f"Error extracting context: {e}")
            return ""
    
    def validate_persian_translation(self, original: str, translated: str) -> Dict:
        """Validate Persian translation quality"""
        try:
            validation_result = {
                'is_valid': True,
                'issues': [],
                'quality_score': 0.0,
                'suggestions': []
            }
            
            # Check if translation contains Persian text
            if not self._contains_persian(translated):
                validation_result['issues'].append('Translation does not contain Persian text')
                validation_result['is_valid'] = False
            
            # Check length ratio (Persian is typically 20-30% longer)
            length_ratio = len(translated) / len(original) if len(original) > 0 else 0
            if length_ratio < 0.5:
                validation_result['issues'].append('Translation seems too short')
                validation_result['suggestions'].append('Check for missing content')
            elif length_ratio > 2.0:
                validation_result['issues'].append('Translation seems too long')
                validation_result['suggestions'].append('Check for redundant content')
            
            # Calculate quality score
            validation_result['quality_score'] = self._calculate_quality_score(original, translated)
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating Persian translation: {e}")
            return {
                'is_valid': False,
                'issues': ['Validation error'],
                'quality_score': 0.0,
                'suggestions': []
            }
    
    def _calculate_quality_score(self, original: str, translated: str) -> float:
        """Calculate quality score for Persian translation"""
        try:
            score = 0.0
            
            # Length ratio check (Persian should be 1.2-1.5x longer)
            length_ratio = len(translated) / len(original) if len(original) > 0 else 0
            if 1.0 <= length_ratio <= 1.8:
                score += 0.3
            
            # Persian character presence
            if self._contains_persian(translated):
                score += 0.4
            
            # Punctuation preservation
            if self._punctuation_preserved(original, translated):
                score += 0.2
            
            # Structure preservation
            if self._structure_preserved(original, translated):
                score += 0.1
            
            return min(score, 1.0)
            
        except Exception as e:
            logger.warning(f"Error calculating quality score: {e}")
            return 0.0
    
    def _punctuation_preserved(self, original: str, translated: str) -> bool:
        """Check if punctuation is preserved"""
        try:
            orig_punct = re.findall(r'[.!?;,]', original)
            trans_punct = re.findall(r'[.!?؛،؟]', translated)
            
            # Simple check - in production, you'd want more sophisticated analysis
            return len(trans_punct) > 0
            
        except Exception as e:
            logger.warning(f"Error checking punctuation preservation: {e}")
            return False
    
    def _structure_preserved(self, original: str, translated: str) -> bool:
        """Check if text structure is preserved"""
        try:
            # Check paragraph breaks
            orig_paragraphs = original.count('\n\n')
            trans_paragraphs = translated.count('\n\n')
            
            # Check sentence count
            orig_sentences = len(re.findall(r'[.!?]', original))
            trans_sentences = len(re.findall(r'[.!؟؟]', translated))
            
            # Simple structure preservation check
            return abs(orig_paragraphs - trans_paragraphs) <= 1 and abs(orig_sentences - trans_sentences) <= 2
            
        except Exception as e:
            logger.warning(f"Error checking structure preservation: {e}")
            return False
    
    def _load_persian_patterns(self) -> Dict:
        """Load Persian text patterns for analysis"""
        return {
            'academic_endings': ['ی', 'ان', 'ات', 'ات'],
            'philosophical_terms': ['وجود', 'حقیقت', 'معنا', 'تجربه'],
            'common_endings': ['است', 'بود', 'شد', 'کرد']
        }
    
    def _load_academic_persian_terms(self) -> List[str]:
        """Load academic Persian terminology"""
        return [
            'وجود', 'حقیقت', 'معنا', 'تجربه', 'آگاهی', 'ذهن', 'روح',
            'فلسفه', 'متافیزیک', 'اپیستمولوژی', 'هرمنوتیک', 'دیالکتیک',
            'پدیدارشناسی', 'وجودگرایی', 'ساختارگرایی', 'پساساختارگرایی',
            'نقد', 'تحلیل', 'تفسیر', 'درک', 'فهم', 'شناخت', 'دانش',
            'حکمت', 'عرفان', 'عقل', 'شعور', 'وجدان', 'ضمیر'
        ]
