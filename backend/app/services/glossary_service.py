# Glossary enforcement service
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re
import logging

from app.models.user_models import Glossary, User
from app.models.models import PDFPage

logger = logging.getLogger(__name__)


class GlossaryEnforcementService:
    """Service for enforcing glossary terms in translations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_user_glossary(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's glossary terms"""
        try:
            glossary_entries = self.db.query(Glossary).filter(
                Glossary.user_id == user_id
            ).all()
            
            return [
                {
                    "id": entry.id,
                    "term": entry.term,
                    "translation": entry.translation,
                    "category": entry.category,
                    "priority": getattr(entry, 'priority', 'medium'),
                    "case_sensitive": getattr(entry, 'case_sensitive', True),
                    "context": getattr(entry, 'context', ''),
                    "created_at": entry.created_at.isoformat() if entry.created_at else None,
                    "updated_at": entry.updated_at.isoformat() if entry.updated_at else None
                }
                for entry in glossary_entries
            ]
            
        except Exception as e:
            logger.error(f"Error getting user glossary: {e}")
            return []
    
    async def enforce_glossary_on_text(
        self,
        text: str, 
        user_id: str,
        strict_mode: bool = False
    ) -> Dict[str, Any]:
        """Enforce glossary terms on a text and return violations and suggestions"""
        try:
            glossary_entries = await self.get_user_glossary(user_id)
            
            violations = []
            suggestions = []
            
            for entry in glossary_entries:
                term = entry["term"]
                translation = entry["translation"]
                priority = entry.get("priority", "medium")
                case_sensitive = entry.get("case_sensitive", True)
                
                # Create search pattern
                pattern = re.escape(term)
                if case_sensitive:
                    text_to_search = text
                    term_to_search = term
                else:
                    text_to_search = text.lower()
                    term_to_search = term.lower()
                
                # Find all occurrences
                if case_sensitive:
                    matches = list(re.finditer(pattern, text, re.IGNORECASE))
                else:
                    matches = list(re.finditer(pattern, text))
                
                for match in matches:
                    start, end = match.span()
                    matched_text = text[start:end]
                    
                    # Check if already translated correctly
                    if matched_text.lower() == translation.lower():
                        continue
                    
                    violation = {
                        "term": term,
                        "matched_text": matched_text,
                        "suggested_translation": translation,
                        "position": start,
                        "length": end - start,
                        "priority": priority,
                        "category": entry.get("category", ""),
                        "context": entry.get("context", ""),
                        "severity": self._calculate_severity(priority, strict_mode)
                    }
                    
                    violations.append(violation)
                    
                    # Create suggestion
                    suggestion = {
                        "type": "glossary",
                        "original_text": matched_text,
                        "suggested_text": translation,
                        "confidence": 0.95,  # High confidence for glossary terms
                        "reason": f"Glossary term '{term}' should be translated as '{translation}'",
                        "glossary_entry_id": entry["id"],
                        "priority": priority,
                        "position": start
                    }
                    
                    suggestions.append(suggestion)
            
            # Sort by severity and position
            violations.sort(key=lambda x: (x["severity"], x["position"]))
            suggestions.sort(key=lambda x: (x["priority"], x["position"]))
            
            return {
                "violations": violations,
                "suggestions": suggestions,
                "violation_count": len(violations),
                "suggestion_count": len(suggestions),
                "enforcement_mode": "strict" if strict_mode else "lenient"
            }
            
        except Exception as e:
            logger.error(f"Error enforcing glossary: {e}")
            return {
                "violations": [],
                "suggestions": [],
                "violation_count": 0,
                "suggestion_count": 0,
                "error": str(e)
            }
    
    async def enforce_glossary_on_page(
        self,
        page_id: int, 
        user_id: str,
        strict_mode: bool = False
    ) -> Dict[str, Any]:
        """Enforce glossary terms on a specific page"""
        try:
            page = self.db.query(PDFPage).filter(PDFPage.id == page_id).first()
            if not page:
                raise ValueError(f"Page {page_id} not found")
            
            if not page.translated_text:
                return {
                    "page_id": page_id,
                    "violations": [],
                    "suggestions": [],
                    "violation_count": 0,
                    "suggestion_count": 0,
                    "message": "No translated text to enforce glossary on"
                }
            
            # Enforce glossary on the translated text
            result = await self.enforce_glossary_on_text(
                page.translated_text, user_id, strict_mode
            )
            
            result["page_id"] = page_id
            result["page_number"] = page.page_number
            result["document_id"] = page.document_id
            
            return result
            
        except Exception as e:
            logger.error(f"Error enforcing glossary on page: {e}")
            return {
                "page_id": page_id,
                "violations": [],
                "suggestions": [],
                "violation_count": 0,
                "suggestion_count": 0,
                "error": str(e)
            }
    
    async def batch_enforce_glossary(
        self,
        document_id: int, 
        user_id: str,
        page_numbers: Optional[List[int]] = None,
        strict_mode: bool = False
    ) -> Dict[str, Any]:
        """Enforce glossary terms on multiple pages"""
        try:
            query = self.db.query(PDFPage).filter(PDFPage.document_id == document_id)
            
            if page_numbers:
                query = query.filter(PDFPage.page_number.in_(page_numbers))
            
            pages = query.all()
            
            results = []
            total_violations = 0
            total_suggestions = 0
            
            for page in pages:
                if page.translated_text:
                    result = await self.enforce_glossary_on_text(
                        page.translated_text, user_id, strict_mode
                    )
                    
                    result["page_id"] = page.id
                    result["page_number"] = page.page_number
                    
                    results.append(result)
                    total_violations += result["violation_count"]
                    total_suggestions += result["suggestion_count"]
            
            return {
                "document_id": document_id,
                "pages_processed": len(results),
                "total_violations": total_violations,
                "total_suggestions": total_suggestions,
                "results": results,
                "enforcement_mode": "strict" if strict_mode else "lenient"
            }
            
        except Exception as e:
            logger.error(f"Error batch enforcing glossary: {e}")
            return {
                "document_id": document_id,
                "pages_processed": 0,
                "total_violations": 0,
                "total_suggestions": 0,
                "results": [],
                "error": str(e)
            }
    
    def _calculate_severity(self, priority: str, strict_mode: bool) -> str:
        """Calculate violation severity based on priority and mode"""
        if strict_mode:
            return "critical"
        
        priority_map = {
            "high": "major",
            "medium": "minor",
            "low": "minor"
        }
        
        return priority_map.get(priority, "minor")
    
    async def get_glossary_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get statistics about user's glossary"""
        try:
            glossary_entries = await self.get_user_glossary(user_id)
            
            if not glossary_entries:
                return {
                    "total_terms": 0,
                    "categories": {},
                    "priority_distribution": {},
                    "case_sensitive_count": 0,
                    "case_insensitive_count": 0
                }
            
            categories = {}
            priority_distribution = {}
            case_sensitive_count = 0
            
            for entry in glossary_entries:
                # Count categories
                category = entry.get("category", "uncategorized")
                categories[category] = categories.get(category, 0) + 1
                
                # Count priorities
                priority = entry.get("priority", "medium")
                priority_distribution[priority] = priority_distribution.get(priority, 0) + 1
                
                # Count case sensitivity
                if entry.get("case_sensitive", True):
                    case_sensitive_count += 1
            
            return {
                "total_terms": len(glossary_entries),
                "categories": categories,
                "priority_distribution": priority_distribution,
                "case_sensitive_count": case_sensitive_count,
                "case_insensitive_count": len(glossary_entries) - case_sensitive_count,
                "most_common_category": max(categories.items(), key=lambda x: x[1])[0] if categories else None,
                "most_common_priority": max(priority_distribution.items(), key=lambda x: x[1])[0] if priority_distribution else None
            }
            
        except Exception as e:
            logger.error(f"Error getting glossary statistics: {e}")
            return {}
    
    async def suggest_glossary_terms(
        self,
        text: str, 
        user_id: str,
        min_frequency: int = 2
    ) -> List[Dict[str, Any]]:
        """Suggest potential glossary terms from text"""
        try:
            # Simple term extraction (in production, use NLP libraries)
            words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
            
            # Count word frequencies
            word_counts = {}
            for word in words:
                if len(word) > 3:  # Only consider words longer than 3 characters
                    word_counts[word] = word_counts.get(word, 0) + 1
            
            # Get existing glossary terms to avoid duplicates
            existing_terms = await self.get_user_glossary(user_id)
            existing_term_set = {entry["term"].lower() for entry in existing_terms}
            
            # Suggest terms that appear frequently and aren't already in glossary
            suggestions = []
            for word, count in word_counts.items():
                if count >= min_frequency and word not in existing_term_set:
                    suggestions.append({
                        "term": word,
                        "frequency": count,
                        "confidence": min(count / 10, 1.0),  # Simple confidence calculation
                        "context": f"Appears {count} times in the text"
                    })
            
            # Sort by frequency and confidence
            suggestions.sort(key=lambda x: (x["frequency"], x["confidence"]), reverse=True)
            
            return suggestions[:20]  # Return top 20 suggestions
            
        except Exception as e:
            logger.error(f"Error suggesting glossary terms: {e}")
            return []