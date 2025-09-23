# Glossary Management Service
# backend/app/services/glossary_service.py

import re
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import logging

from app.models.user_models import Glossary, User
from app.services.term_extractor import TermExtractor

logger = logging.getLogger(__name__)

class GlossaryService:
    """Service for managing user glossaries and terminology"""
    
    def __init__(self):
        self.term_extractor = TermExtractor()
    
    def create_glossary_entry(
        self,
        user_id: int,
        term: str,
        translation: str,
        context: Optional[str] = None,
        category: Optional[str] = None,
        db: Session
    ) -> Dict[str, Any]:
        """Create a new glossary entry"""
        try:
            # Check if user exists
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return {
                    "success": False,
                    "error": "User not found"
                }
            
            # Check if term already exists for this user
            existing_entry = db.query(Glossary).filter(
                and_(
                    Glossary.user_id == user_id,
                    Glossary.term == term.lower().strip()
                )
            ).first()
            
            if existing_entry:
                return {
                    "success": False,
                    "error": "Term already exists in your glossary"
                }
            
            # Create new glossary entry
            new_entry = Glossary(
                user_id=user_id,
                term=term.lower().strip(),
                translation=translation.strip(),
                context=context,
                category=category,
                confidence_score=1.0
            )
            
            db.add(new_entry)
            db.commit()
            db.refresh(new_entry)
            
            return {
                "success": True,
                "glossary": {
                    "id": new_entry.id,
                    "uuid": new_entry.uuid,
                    "term": new_entry.term,
                    "translation": new_entry.translation,
                    "context": new_entry.context,
                    "category": new_entry.category,
                    "confidence_score": new_entry.confidence_score,
                    "created_at": new_entry.created_at
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to create glossary entry: {e}")
            db.rollback()
            return {
                "success": False,
                "error": "Failed to create glossary entry"
            }
    
    def get_user_glossary(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Get all glossary entries for a user"""
        try:
            entries = db.query(Glossary).filter(
                Glossary.user_id == user_id
            ).order_by(Glossary.created_at.desc()).all()
            
            glossary_data = []
            for entry in entries:
                glossary_data.append({
                    "id": entry.id,
                    "uuid": entry.uuid,
                    "term": entry.term,
                    "translation": entry.translation,
                    "context": entry.context,
                    "category": entry.category,
                    "usage_count": entry.usage_count,
                    "confidence_score": entry.confidence_score,
                    "user_rating": entry.user_rating,
                    "created_at": entry.created_at,
                    "last_used": entry.last_used
                })
            
            return {
                "success": True,
                "glossary": glossary_data,
                "total_count": len(glossary_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to get user glossary: {e}")
            return {
                "success": False,
                "error": "Failed to retrieve glossary"
            }
    
    def update_glossary_entry(
        self,
        entry_id: int,
        user_id: int,
        translation: Optional[str] = None,
        context: Optional[str] = None,
        category: Optional[str] = None,
        user_rating: Optional[int] = None,
        db: Session
    ) -> Dict[str, Any]:
        """Update a glossary entry"""
        try:
            entry = db.query(Glossary).filter(
                and_(
                    Glossary.id == entry_id,
                    Glossary.user_id == user_id
                )
            ).first()
            
            if not entry:
                return {
                    "success": False,
                    "error": "Glossary entry not found"
                }
            
            # Update fields if provided
            if translation is not None:
                entry.translation = translation.strip()
            if context is not None:
                entry.context = context
            if category is not None:
                entry.category = category
            if user_rating is not None:
                entry.user_rating = user_rating
            
            entry.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(entry)
            
            return {
                "success": True,
                "glossary": {
                    "id": entry.id,
                    "uuid": entry.uuid,
                    "term": entry.term,
                    "translation": entry.translation,
                    "context": entry.context,
                    "category": entry.category,
                    "user_rating": entry.user_rating,
                    "updated_at": entry.updated_at
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to update glossary entry: {e}")
            db.rollback()
            return {
                "success": False,
                "error": "Failed to update glossary entry"
            }
    
    def delete_glossary_entry(self, entry_id: int, user_id: int, db: Session) -> Dict[str, Any]:
        """Delete a glossary entry"""
        try:
            entry = db.query(Glossary).filter(
                and_(
                    Glossary.id == entry_id,
                    Glossary.user_id == user_id
                )
            ).first()
            
            if not entry:
                return {
                    "success": False,
                    "error": "Glossary entry not found"
                }
            
            db.delete(entry)
            db.commit()
            
            return {
                "success": True,
                "message": "Glossary entry deleted successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to delete glossary entry: {e}")
            db.rollback()
            return {
                "success": False,
                "error": "Failed to delete glossary entry"
            }
    
    def search_glossary_entries(
        self,
        user_id: int,
        search_term: str,
        category: Optional[str] = None,
        db: Session
    ) -> Dict[str, Any]:
        """Search glossary entries"""
        try:
            query = db.query(Glossary).filter(Glossary.user_id == user_id)
            
            # Add search term filter
            if search_term:
                search_pattern = f"%{search_term.lower()}%"
                query = query.filter(
                    or_(
                        Glossary.term.ilike(search_pattern),
                        Glossary.translation.ilike(search_pattern),
                        Glossary.context.ilike(search_pattern)
                    )
                )
            
            # Add category filter
            if category:
                query = query.filter(Glossary.category == category)
            
            entries = query.order_by(Glossary.created_at.desc()).all()
            
            glossary_data = []
            for entry in entries:
                glossary_data.append({
                    "id": entry.id,
                    "uuid": entry.uuid,
                    "term": entry.term,
                    "translation": entry.translation,
                    "context": entry.context,
                    "category": entry.category,
                    "usage_count": entry.usage_count,
                    "confidence_score": entry.confidence_score,
                    "created_at": entry.created_at
                })
            
            return {
                "success": True,
                "glossary": glossary_data,
                "total_count": len(glossary_data),
                "search_term": search_term,
                "category": category
            }
            
        except Exception as e:
            logger.error(f"Failed to search glossary entries: {e}")
            return {
                "success": False,
                "error": "Failed to search glossary entries"
            }
    
    def get_glossary_by_category(self, user_id: int, category: str, db: Session) -> Dict[str, Any]:
        """Get glossary entries by category"""
        try:
            entries = db.query(Glossary).filter(
                and_(
                    Glossary.user_id == user_id,
                    Glossary.category == category
                )
            ).order_by(Glossary.created_at.desc()).all()
            
            glossary_data = []
            for entry in entries:
                glossary_data.append({
                    "id": entry.id,
                    "uuid": entry.uuid,
                    "term": entry.term,
                    "translation": entry.translation,
                    "context": entry.context,
                    "category": entry.category,
                    "usage_count": entry.usage_count,
                    "confidence_score": entry.confidence_score,
                    "created_at": entry.created_at
                })
            
            return {
                "success": True,
                "glossary": glossary_data,
                "category": category,
                "total_count": len(glossary_data)
            }
            
        except Exception as e:
            logger.error(f"Failed to get glossary by category: {e}")
            return {
                "success": False,
                "error": "Failed to retrieve glossary by category"
            }
    
    def extract_terms_from_document(
        self,
        user_id: int,
        document_text: str,
        db: Session
    ) -> Dict[str, Any]:
        """Extract terms from document and suggest glossary entries"""
        try:
            # Extract terms using term extractor
            extraction_result = self.term_extractor.extract_terms_from_text(document_text)
            
            if not extraction_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to extract terms from document"
                }
            
            # Get existing user glossary
            existing_glossary = self.get_user_glossary(user_id, db)
            existing_terms = set()
            if existing_glossary["success"]:
                existing_terms = {entry["term"] for entry in existing_glossary["glossary"]}
            
            # Filter out existing terms
            new_terms = []
            for term_data in extraction_result["terms"]:
                if term_data["term"].lower() not in existing_terms:
                    new_terms.append(term_data)
            
            return {
                "success": True,
                "extracted_terms": extraction_result["terms"],
                "new_terms": new_terms,
                "existing_terms": list(existing_terms),
                "total_extracted": len(extraction_result["terms"]),
                "new_count": len(new_terms)
            }
            
        except Exception as e:
            logger.error(f"Failed to extract terms from document: {e}")
            return {
                "success": False,
                "error": "Failed to extract terms from document"
            }
    
    def suggest_translations(self, terms: List[str], db: Session) -> Dict[str, Any]:
        """Suggest translations for terms"""
        try:
            suggestions = self.term_extractor.suggest_translations(terms)
            
            return {
                "success": True,
                "suggestions": suggestions["suggestions"]
            }
            
        except Exception as e:
            logger.error(f"Failed to suggest translations: {e}")
            return {
                "success": False,
                "error": "Failed to suggest translations"
            }
    
    def check_translation_consistency(
        self,
        user_id: int,
        document_text: str,
        db: Session
    ) -> Dict[str, Any]:
        """Check translation consistency using user's glossary"""
        try:
            # Get user glossary
            glossary_result = self.get_user_glossary(user_id, db)
            if not glossary_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to retrieve user glossary"
                }
            
            user_glossary = glossary_result["glossary"]
            
            # Extract terms from document
            extraction_result = self.extract_terms_from_document(user_id, document_text, db)
            if not extraction_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to extract terms from document"
                }
            
            # Check consistency
            matched_terms = []
            unmatched_terms = []
            
            for term_data in extraction_result["extracted_terms"]:
                term = term_data["term"].lower()
                found_match = False
                
                for glossary_entry in user_glossary:
                    if glossary_entry["term"].lower() == term:
                        matched_terms.append({
                            "term": term,
                            "glossary_translation": glossary_entry["translation"],
                            "context": term_data.get("context"),
                            "confidence": glossary_entry["confidence_score"]
                        })
                        found_match = True
                        break
                
                if not found_match:
                    unmatched_terms.append({
                        "term": term,
                        "context": term_data.get("context"),
                        "suggested_category": term_data.get("category")
                    })
            
            # Calculate consistency score
            total_terms = len(extraction_result["extracted_terms"])
            matched_count = len(matched_terms)
            consistency_score = (matched_count / total_terms * 100) if total_terms > 0 else 0
            
            return {
                "success": True,
                "consistency_score": round(consistency_score, 2),
                "matched_terms": matched_terms,
                "unmatched_terms": unmatched_terms,
                "total_terms": total_terms,
                "matched_count": matched_count,
                "unmatched_count": len(unmatched_terms)
            }
            
        except Exception as e:
            logger.error(f"Failed to check translation consistency: {e}")
            return {
                "success": False,
                "error": "Failed to check translation consistency"
            }
    
    def apply_glossary_to_translation(
        self,
        user_id: int,
        original_text: str,
        translated_text: str,
        db: Session
    ) -> Dict[str, Any]:
        """Apply glossary to translation for consistency"""
        try:
            # Get user glossary
            glossary_result = self.get_user_glossary(user_id, db)
            if not glossary_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to retrieve user glossary"
                }
            
            user_glossary = glossary_result["glossary"]
            
            # Apply glossary terms to translation
            corrected_translation = translated_text
            applied_terms = []
            
            for glossary_entry in user_glossary:
                term = glossary_entry["term"]
                translation = glossary_entry["translation"]
                
                # Simple term replacement (in production, use more sophisticated NLP)
                if term.lower() in original_text.lower():
                    # Replace in translated text if found
                    if term.lower() in corrected_translation.lower():
                        corrected_translation = corrected_translation.replace(
                            term.lower(), translation
                        )
                        applied_terms.append({
                            "term": term,
                            "translation": translation,
                            "context": glossary_entry["context"]
                        })
            
            # Calculate consistency score
            consistency_result = self.check_translation_consistency(
                user_id, original_text, db
            )
            
            return {
                "success": True,
                "corrected_translation": corrected_translation,
                "applied_terms": applied_terms,
                "consistency_score": consistency_result.get("consistency_score", 0),
                "original_translation": translated_text
            }
            
        except Exception as e:
            logger.error(f"Failed to apply glossary to translation: {e}")
            return {
                "success": False,
                "error": "Failed to apply glossary to translation"
            }
    
    def export_glossary(
        self,
        user_id: int,
        format: str = "json",
        category: Optional[str] = None,
        db: Session
    ) -> Dict[str, Any]:
        """Export glossary in specified format"""
        try:
            # Get glossary data
            if category:
                glossary_result = self.get_glossary_by_category(user_id, category, db)
            else:
                glossary_result = self.get_user_glossary(user_id, db)
            
            if not glossary_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to retrieve glossary"
                }
            
            glossary_data = glossary_result["glossary"]
            
            # Export in requested format
            if format.lower() == "json":
                export_data = {
                    "glossary": glossary_data,
                    "export_date": datetime.utcnow().isoformat(),
                    "total_entries": len(glossary_data),
                    "category": category
                }
                data = json.dumps(export_data, indent=2, ensure_ascii=False)
                
            elif format.lower() == "csv":
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow(["Term", "Translation", "Context", "Category", "Created At"])
                
                # Write data
                for entry in glossary_data:
                    writer.writerow([
                        entry["term"],
                        entry["translation"],
                        entry["context"] or "",
                        entry["category"] or "",
                        entry["created_at"]
                    ])
                
                data = output.getvalue()
                output.close()
                
            else:
                return {
                    "success": False,
                    "error": "Unsupported export format"
                }
            
            return {
                "success": True,
                "data": data,
                "format": format,
                "total_entries": len(glossary_data),
                "category": category
            }
            
        except Exception as e:
            logger.error(f"Failed to export glossary: {e}")
            return {
                "success": False,
                "error": "Failed to export glossary"
            }
    
    def import_glossary(
        self,
        user_id: int,
        data: List[Dict[str, Any]],
        db: Session
    ) -> Dict[str, Any]:
        """Import glossary entries from data"""
        try:
            imported_count = 0
            skipped_count = 0
            errors = []
            
            for entry_data in data:
                try:
                    # Validate required fields
                    if not entry_data.get("term") or not entry_data.get("translation"):
                        skipped_count += 1
                        errors.append(f"Missing required fields: {entry_data}")
                        continue
                    
                    # Check if term already exists
                    existing_entry = db.query(Glossary).filter(
                        and_(
                            Glossary.user_id == user_id,
                            Glossary.term == entry_data["term"].lower().strip()
                        )
                    ).first()
                    
                    if existing_entry:
                        skipped_count += 1
                        continue
                    
                    # Create new entry
                    new_entry = Glossary(
                        user_id=user_id,
                        term=entry_data["term"].lower().strip(),
                        translation=entry_data["translation"].strip(),
                        context=entry_data.get("context"),
                        category=entry_data.get("category"),
                        confidence_score=entry_data.get("confidence_score", 1.0)
                    )
                    
                    db.add(new_entry)
                    imported_count += 1
                    
                except Exception as e:
                    skipped_count += 1
                    errors.append(f"Error importing entry {entry_data}: {str(e)}")
            
            db.commit()
            
            return {
                "success": True,
                "imported_count": imported_count,
                "skipped_count": skipped_count,
                "total_processed": len(data),
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Failed to import glossary: {e}")
            db.rollback()
            return {
                "success": False,
                "error": "Failed to import glossary"
            }
    
    def generate_consistency_report(self, user_id: int, db: Session) -> Dict[str, Any]:
        """Generate consistency report for user's glossary"""
        try:
            # Get user glossary
            glossary_result = self.get_user_glossary(user_id, db)
            if not glossary_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to retrieve user glossary"
                }
            
            glossary_data = glossary_result["glossary"]
            
            # Calculate statistics
            total_terms = len(glossary_data)
            categories = {}
            avg_confidence = 0
            rated_entries = 0
            
            for entry in glossary_data:
                # Category breakdown
                category = entry["category"] or "uncategorized"
                categories[category] = categories.get(category, 0) + 1
                
                # Confidence score
                avg_confidence += entry["confidence_score"]
                
                # User ratings
                if entry["user_rating"]:
                    rated_entries += 1
            
            avg_confidence = avg_confidence / total_terms if total_terms > 0 else 0
            
            # Generate recommendations
            recommendations = []
            if avg_confidence < 0.8:
                recommendations.append("Consider reviewing low-confidence entries")
            if rated_entries < total_terms * 0.5:
                recommendations.append("Rate more entries to improve quality")
            if "uncategorized" in categories:
                recommendations.append("Categorize uncategorized terms")
            
            return {
                "success": True,
                "total_terms": total_terms,
                "consistency_score": round(avg_confidence * 100, 2),
                "category_breakdown": categories,
                "average_confidence": round(avg_confidence, 2),
                "rated_entries": rated_entries,
                "rating_coverage": round((rated_entries / total_terms * 100), 2) if total_terms > 0 else 0,
                "recommendations": recommendations
            }
            
        except Exception as e:
            logger.error(f"Failed to generate consistency report: {e}")
            return {
                "success": False,
                "error": "Failed to generate consistency report"
            }
