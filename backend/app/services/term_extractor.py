# Term Extractor Service
# backend/app/services/term_extractor.py

import re
import nltk
from typing import Dict, List, Any, Optional
from collections import Counter
import logging

logger = logging.getLogger(__name__)

class TermExtractor:
    """Service for extracting terms from documents and suggesting translations"""
    
    def __init__(self):
        self.academic_terms = self._load_academic_terms()
        self.philosophical_concepts = self._load_philosophical_concepts()
        self.technical_terms = self._load_technical_terms()
        
        # Download required NLTK data
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
        
        try:
            nltk.data.find('taggers/averaged_perceptron_tagger')
        except LookupError:
            nltk.download('averaged_perceptron_tagger')
    
    def _load_academic_terms(self) -> List[str]:
        """Load academic terminology"""
        return [
            "methodology", "paradigm", "framework", "theoretical", "empirical",
            "hypothesis", "analysis", "synthesis", "evaluation", "assessment",
            "critique", "interpretation", "examination", "investigation", "research",
            "study", "scholarship", "academic", "scholarly", "intellectual",
            "conceptual", "analytical", "systematic", "comprehensive", "rigorous"
        ]
    
    def _load_philosophical_concepts(self) -> List[str]:
        """Load philosophical concepts"""
        return [
            "existentialism", "phenomenology", "ontology", "epistemology", "metaphysics",
            "ethics", "aesthetics", "logic", "dialectic", "hermeneutics",
            "deconstruction", "postmodernism", "structuralism", "pragmatism", "idealism",
            "materialism", "dualism", "monism", "determinism", "free will",
            "consciousness", "subjectivity", "objectivity", "truth", "reality",
            "being", "existence", "essence", "substance", "accident"
        ]
    
    def _load_technical_terms(self) -> List[str]:
        """Load technical terminology"""
        return [
            "algorithm", "implementation", "optimization", "configuration", "architecture",
            "framework", "protocol", "interface", "specification", "documentation",
            "deployment", "integration", "validation", "verification", "testing",
            "debugging", "monitoring", "analytics", "metrics", "performance"
        ]
    
    def extract_terms_from_text(self, text: str) -> Dict[str, Any]:
        """Extract terms from document text"""
        try:
            # Clean and preprocess text
            cleaned_text = self._clean_text(text)
            
            # Extract different types of terms
            academic_terms = self._extract_academic_terms(cleaned_text)
            philosophical_terms = self._extract_philosophical_terms(cleaned_text)
            technical_terms = self._extract_technical_terms(cleaned_text)
            proper_nouns = self._extract_proper_nouns(cleaned_text)
            compound_terms = self._extract_compound_terms(cleaned_text)
            
            # Combine all terms
            all_terms = []
            all_terms.extend(academic_terms)
            all_terms.extend(philosophical_terms)
            all_terms.extend(technical_terms)
            all_terms.extend(proper_nouns)
            all_terms.extend(compound_terms)
            
            # Remove duplicates and sort by frequency
            term_counts = Counter([term["term"] for term in all_terms])
            unique_terms = []
            
            for term, count in term_counts.most_common():
                # Find the first occurrence to get context
                for term_data in all_terms:
                    if term_data["term"] == term:
                        term_data["frequency"] = count
                        unique_terms.append(term_data)
                        break
            
            return {
                "success": True,
                "terms": unique_terms,
                "total_terms": len(unique_terms),
                "academic_count": len(academic_terms),
                "philosophical_count": len(philosophical_terms),
                "technical_count": len(technical_terms),
                "proper_nouns_count": len(proper_nouns),
                "compound_terms_count": len(compound_terms)
            }
            
        except Exception as e:
            logger.error(f"Failed to extract terms from text: {e}")
            return {
                "success": False,
                "error": "Failed to extract terms from text"
            }
    
    def extract_academic_terms(self, text: str) -> Dict[str, Any]:
        """Extract academic terms specifically"""
        try:
            cleaned_text = self._clean_text(text)
            academic_terms = self._extract_academic_terms(cleaned_text)
            
            return {
                "success": True,
                "terms": academic_terms,
                "total_count": len(academic_terms)
            }
            
        except Exception as e:
            logger.error(f"Failed to extract academic terms: {e}")
            return {
                "success": False,
                "error": "Failed to extract academic terms"
            }
    
    def suggest_translations(self, terms: List[str]) -> Dict[str, Any]:
        """Suggest translations for extracted terms"""
        try:
            suggestions = []
            
            for term in terms:
                suggestion = self._suggest_translation_for_term(term)
                suggestions.append(suggestion)
            
            return {
                "success": True,
                "suggestions": suggestions
            }
            
        except Exception as e:
            logger.error(f"Failed to suggest translations: {e}")
            return {
                "success": False,
                "error": "Failed to suggest translations"
            }
    
    def detect_term_consistency(self, document_terms: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect term consistency across documents"""
        try:
            # Group terms by base form
            term_groups = {}
            for term_data in document_terms:
                term = term_data["term"].lower()
                base_form = self._get_base_form(term)
                
                if base_form not in term_groups:
                    term_groups[base_form] = []
                term_groups[base_form].append(term_data)
            
            # Analyze consistency
            consistent_terms = []
            inconsistent_terms = []
            
            for base_form, terms in term_groups.items():
                if len(terms) > 1:
                    # Check if all variations are consistent
                    contexts = [term.get("context", "") for term in terms]
                    if len(set(contexts)) == 1:  # All contexts are the same
                        consistent_terms.append({
                            "base_form": base_form,
                            "variations": [term["term"] for term in terms],
                            "context": contexts[0],
                            "count": len(terms)
                        })
                    else:
                        inconsistent_terms.append({
                            "base_form": base_form,
                            "variations": [term["term"] for term in terms],
                            "contexts": contexts,
                            "count": len(terms)
                        })
            
            # Calculate consistency score
            total_term_instances = sum(len(terms) for terms in term_groups.values())
            consistent_instances = sum(term["count"] for term in consistent_terms)
            consistency_score = (consistent_instances / total_term_instances * 100) if total_term_instances > 0 else 0
            
            return {
                "success": True,
                "consistency_score": round(consistency_score, 2),
                "consistent_terms": consistent_terms,
                "inconsistent_terms": inconsistent_terms,
                "total_term_instances": total_term_instances,
                "consistent_instances": consistent_instances
            }
            
        except Exception as e:
            logger.error(f"Failed to detect term consistency: {e}")
            return {
                "success": False,
                "error": "Failed to detect term consistency"
            }
    
    def validate_term_translation(self, term_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate term translation"""
        try:
            term = term_data["term"]
            translation = term_data["translation"]
            context = term_data.get("context", "")
            
            # Basic validation checks
            is_valid = True
            confidence = 1.0
            suggestions = []
            
            # Check if translation is empty
            if not translation or not translation.strip():
                is_valid = False
                suggestions.append("Translation cannot be empty")
                confidence = 0.0
            
            # Check if translation is too similar to original
            elif term.lower() == translation.lower():
                is_valid = False
                suggestions.append("Translation should be different from original term")
                confidence = 0.3
            
            # Check if translation contains only English characters (for Persian translation)
            elif re.match(r'^[a-zA-Z\s]+$', translation):
                suggestions.append("Consider using Persian characters for better translation")
                confidence = 0.7
            
            # Check length ratio
            length_ratio = len(translation) / len(term) if len(term) > 0 else 1
            if length_ratio < 0.5 or length_ratio > 3:
                suggestions.append("Translation length seems unusual")
                confidence = min(confidence, 0.8)
            
            return {
                "success": True,
                "is_valid": is_valid,
                "confidence": confidence,
                "suggestions": suggestions,
                "validation_details": {
                    "length_ratio": length_ratio,
                    "has_translation": bool(translation and translation.strip()),
                    "different_from_original": term.lower() != translation.lower()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to validate term translation: {e}")
            return {
                "success": False,
                "error": "Failed to validate term translation"
            }
    
    def _clean_text(self, text: str) -> str:
        """Clean and preprocess text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,!?;:()\[\]{}"\'-]', '', text)
        
        return text.strip()
    
    def _extract_academic_terms(self, text: str) -> List[Dict[str, Any]]:
        """Extract academic terms from text"""
        terms = []
        text_lower = text.lower()
        
        for term in self.academic_terms:
            if term.lower() in text_lower:
                # Find context around the term
                context = self._get_term_context(text, term)
                terms.append({
                    "term": term,
                    "category": "academic",
                    "context": context,
                    "confidence": 0.9
                })
        
        return terms
    
    def _extract_philosophical_terms(self, text: str) -> List[Dict[str, Any]]:
        """Extract philosophical terms from text"""
        terms = []
        text_lower = text.lower()
        
        for term in self.philosophical_concepts:
            if term.lower() in text_lower:
                context = self._get_term_context(text, term)
                terms.append({
                    "term": term,
                    "category": "philosophy",
                    "context": context,
                    "confidence": 0.95
                })
        
        return terms
    
    def _extract_technical_terms(self, text: str) -> List[Dict[str, Any]]:
        """Extract technical terms from text"""
        terms = []
        text_lower = text.lower()
        
        for term in self.technical_terms:
            if term.lower() in text_lower:
                context = self._get_term_context(text, term)
                terms.append({
                    "term": term,
                    "category": "technical",
                    "context": context,
                    "confidence": 0.85
                })
        
        return terms
    
    def _extract_proper_nouns(self, text: str) -> List[Dict[str, Any]]:
        """Extract proper nouns from text"""
        try:
            import nltk
            tokens = nltk.word_tokenize(text)
            pos_tags = nltk.pos_tag(tokens)
            
            proper_nouns = []
            for token, pos in pos_tags:
                if pos in ['NNP', 'NNPS']:  # Proper nouns
                    if len(token) > 2:  # Filter out short tokens
                        context = self._get_term_context(text, token)
                        proper_nouns.append({
                            "term": token,
                            "category": "proper_noun",
                            "context": context,
                            "confidence": 0.8
                        })
            
            return proper_nouns
            
        except Exception as e:
            logger.warning(f"Failed to extract proper nouns: {e}")
            return []
    
    def _extract_compound_terms(self, text: str) -> List[Dict[str, Any]]:
        """Extract compound terms (multi-word phrases)"""
        try:
            import nltk
            tokens = nltk.word_tokenize(text)
            pos_tags = nltk.pos_tag(tokens)
            
            compound_terms = []
            i = 0
            while i < len(pos_tags) - 1:
                if (pos_tags[i][1] in ['NN', 'NNS'] and 
                    pos_tags[i + 1][1] in ['NN', 'NNS']):
                    
                    # Found potential compound term
                    term = f"{pos_tags[i][0]} {pos_tags[i + 1][0]}"
                    context = self._get_term_context(text, term)
                    
                    compound_terms.append({
                        "term": term,
                        "category": "compound",
                        "context": context,
                        "confidence": 0.7
                    })
                    i += 2
                else:
                    i += 1
            
            return compound_terms
            
        except Exception as e:
            logger.warning(f"Failed to extract compound terms: {e}")
            return []
    
    def _get_term_context(self, text: str, term: str, context_length: int = 50) -> str:
        """Get context around a term"""
        try:
            term_lower = term.lower()
            text_lower = text.lower()
            
            # Find the position of the term
            pos = text_lower.find(term_lower)
            if pos == -1:
                return ""
            
            # Extract context
            start = max(0, pos - context_length)
            end = min(len(text), pos + len(term) + context_length)
            
            context = text[start:end]
            
            # Highlight the term in context
            highlighted_context = context.replace(term, f"**{term}**")
            
            return highlighted_context
            
        except Exception as e:
            logger.warning(f"Failed to get term context: {e}")
            return ""
    
    def _get_base_form(self, term: str) -> str:
        """Get base form of a term (simple stemming)"""
        # Simple stemming for common English patterns
        term = term.lower()
        
        # Remove common suffixes
        suffixes = ['ing', 'ed', 's', 'es', 'ly', 'tion', 'sion', 'ness', 'ment']
        for suffix in suffixes:
            if term.endswith(suffix):
                term = term[:-len(suffix)]
                break
        
        return term
    
    def _suggest_translation_for_term(self, term: str) -> Dict[str, Any]:
        """Suggest translation for a specific term"""
        # This is a placeholder - in production, you'd use:
        # 1. Pre-built translation dictionaries
        # 2. Machine translation APIs
        # 3. User's existing glossary
        # 4. Context-aware translation models
        
        suggestions = {
            "existentialism": "وجودگرایی",
            "phenomenology": "پدیدارشناسی",
            "ontology": "هستی‌شناسی",
            "epistemology": "شناخت‌شناسی",
            "metaphysics": "مابعدالطبیعه",
            "methodology": "روش‌شناسی",
            "paradigm": "الگو",
            "framework": "چارچوب",
            "analysis": "تحلیل",
            "synthesis": "ترکیب"
        }
        
        suggested_translation = suggestions.get(term.lower(), "")
        confidence = 0.9 if suggested_translation else 0.3
        
        return {
            "term": term,
            "translation": suggested_translation,
            "confidence": confidence,
            "category": self._categorize_term(term),
            "source": "dictionary" if suggested_translation else "unknown"
        }
    
    def _categorize_term(self, term: str) -> str:
        """Categorize a term"""
        term_lower = term.lower()
        
        if term_lower in self.philosophical_concepts:
            return "philosophy"
        elif term_lower in self.academic_terms:
            return "academic"
        elif term_lower in self.technical_terms:
            return "technical"
        elif term_lower.istitle():
            return "proper_noun"
        else:
            return "general"
