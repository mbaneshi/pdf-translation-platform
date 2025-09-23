# Quality scoring service for translation evaluation
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import re
import logging

from app.models.models import PDFPage
from app.models.user_models import User

logger = logging.getLogger(__name__)


class QualityScoringService:
    """Service for evaluating translation quality"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def score_translation(
        self, 
        original_text: str, 
        translated_text: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Score a translation across multiple quality dimensions"""
        try:
            scores = {}
            
            # Adequacy Score (content preservation)
            scores["adequacy"] = await self._calculate_adequacy_score(original_text, translated_text)
            
            # Fluency Score (target language quality)
            scores["fluency"] = await self._calculate_fluency_score(translated_text)
            
            # Consistency Score (terminology consistency)
            scores["consistency"] = await self._calculate_consistency_score(translated_text, user_id)
            
            # Formatting Score (preservation of formatting)
            scores["formatting"] = await self._calculate_formatting_score(original_text, translated_text)
            
            # Overall Score (weighted average)
            weights = {
                "adequacy": 0.3,
                "fluency": 0.25,
                "consistency": 0.25,
                "formatting": 0.2
            }
            
            overall_score = sum(scores[dim] * weights[dim] for dim in scores)
            scores["overall"] = round(overall_score, 2)
            
            # Quality Level
            scores["quality_level"] = self._get_quality_level(scores["overall"])
            
            # Detailed analysis
            scores["analysis"] = {
                "word_count_original": len(original_text.split()),
                "word_count_translated": len(translated_text.split()),
                "character_count_original": len(original_text),
                "character_count_translated": len(translated_text),
                "expansion_ratio": len(translated_text) / len(original_text) if original_text else 0,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return scores
            
        except Exception as e:
            logger.error(f"Error scoring translation: {e}")
            return {
                "adequacy": 0.0,
                "fluency": 0.0,
                "consistency": 0.0,
                "formatting": 0.0,
                "overall": 0.0,
                "quality_level": "poor",
                "error": str(e)
            }
    
    async def score_page(self, page_id: int, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Score a specific page's translation"""
        try:
            page = self.db.query(PDFPage).filter(PDFPage.id == page_id).first()
            if not page:
                raise ValueError(f"Page {page_id} not found")
            
            if not page.translated_text:
                return {
                    "page_id": page_id,
                    "scores": {
                        "overall": 0.0,
                        "quality_level": "no_translation",
                        "message": "No translation available to score"
                    }
                }
            
            scores = await self.score_translation(
                page.original_text, 
                page.translated_text, 
                user_id
            )
            
            # Update page with quality score
            page.quality_score = scores["overall"]
            self.db.commit()
            
            return {
                "page_id": page_id,
                "page_number": page.page_number,
                "document_id": page.document_id,
                "scores": scores
            }
            
        except Exception as e:
            logger.error(f"Error scoring page: {e}")
            return {
                "page_id": page_id,
                "scores": {
                    "overall": 0.0,
                    "quality_level": "error",
                    "error": str(e)
                }
            }
    
    async def score_document(
        self, 
        document_id: int, 
        user_id: Optional[str] = None,
        page_numbers: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Score all pages in a document"""
        try:
            query = self.db.query(PDFPage).filter(PDFPage.document_id == document_id)
            
            if page_numbers:
                query = query.filter(PDFPage.page_number.in_(page_numbers))
            
            pages = query.all()
            
            page_scores = []
            total_score = 0
            scored_pages = 0
            
            for page in pages:
                if page.translated_text:
                    page_result = await self.score_page(page.id, user_id)
                    page_scores.append(page_result)
                    total_score += page_result["scores"]["overall"]
                    scored_pages += 1
            
            # Calculate document-level metrics
            average_score = total_score / scored_pages if scored_pages > 0 else 0
            
            # Quality distribution
            quality_distribution = {
                "excellent": 0,
                "good": 0,
                "fair": 0,
                "poor": 0
            }
            
            for page_result in page_scores:
                quality_level = page_result["scores"]["quality_level"]
                if quality_level in quality_distribution:
                    quality_distribution[quality_level] += 1
            
            return {
                "document_id": document_id,
                "total_pages": len(pages),
                "scored_pages": scored_pages,
                "average_score": round(average_score, 2),
                "quality_distribution": quality_distribution,
                "page_scores": page_scores,
                "overall_quality_level": self._get_quality_level(average_score)
            }
            
        except Exception as e:
            logger.error(f"Error scoring document: {e}")
            return {
                "document_id": document_id,
                "total_pages": 0,
                "scored_pages": 0,
                "average_score": 0.0,
                "quality_distribution": {},
                "page_scores": [],
                "error": str(e)
            }
    
    async def _calculate_adequacy_score(self, original: str, translated: str) -> float:
        """Calculate adequacy score (content preservation)"""
        try:
            # Simple heuristic-based scoring
            # In production, use more sophisticated methods like BLEU, METEOR, etc.
            
            original_words = set(original.lower().split())
            translated_words = set(translated.lower().split())
            
            # Word overlap ratio
            if not original_words:
                return 0.0
            
            overlap = len(original_words.intersection(translated_words))
            word_overlap_score = overlap / len(original_words)
            
            # Length ratio (should be reasonable)
            length_ratio = len(translated) / len(original) if original else 0
            length_score = 1.0 - abs(length_ratio - 1.2) / 2.0  # Optimal around 1.2
            length_score = max(0, min(1, length_score))
            
            # Combine scores
            adequacy_score = (word_overlap_score * 0.6 + length_score * 0.4)
            return min(1.0, max(0.0, adequacy_score))
            
        except Exception as e:
            logger.error(f"Error calculating adequacy score: {e}")
            return 0.0
    
    async def _calculate_fluency_score(self, translated_text: str) -> float:
        """Calculate fluency score (target language quality)"""
        try:
            # Simple heuristic-based scoring
            # In production, use language models or fluency classifiers
            
            words = translated_text.split()
            if not words:
                return 0.0
            
            # Average word length (reasonable for Persian)
            avg_word_length = sum(len(word) for word in words) / len(words)
            word_length_score = 1.0 - abs(avg_word_length - 5) / 10.0
            word_length_score = max(0, min(1, word_length_score))
            
            # Sentence structure (simple check for proper punctuation)
            sentences = re.split(r'[.!?]+', translated_text)
            proper_sentences = sum(1 for s in sentences if len(s.strip()) > 0)
            sentence_score = min(1.0, proper_sentences / max(1, len(sentences)))
            
            # Character diversity (avoid repetitive characters)
            unique_chars = len(set(translated_text.lower()))
            char_diversity_score = min(1.0, unique_chars / 50.0)
            
            # Combine scores
            fluency_score = (word_length_score * 0.4 + sentence_score * 0.4 + char_diversity_score * 0.2)
            return min(1.0, max(0.0, fluency_score))
            
        except Exception as e:
            logger.error(f"Error calculating fluency score: {e}")
            return 0.0
    
    async def _calculate_consistency_score(self, translated_text: str, user_id: Optional[str] = None) -> float:
        """Calculate consistency score (terminology consistency)"""
        try:
            # For now, return a mock score
            # In production, check against glossary and previous translations
            
            words = translated_text.lower().split()
            if not words:
                return 0.0
            
            # Simple consistency check (word frequency analysis)
            word_counts = {}
            for word in words:
                if len(word) > 3:  # Only consider meaningful words
                    word_counts[word] = word_counts.get(word, 0) + 1
            
            # Calculate consistency based on repeated terms
            total_words = len(words)
            repeated_words = sum(count for count in word_counts.values() if count > 1)
            
            consistency_score = repeated_words / total_words if total_words > 0 else 0.0
            return min(1.0, max(0.0, consistency_score))
            
        except Exception as e:
            logger.error(f"Error calculating consistency score: {e}")
            return 0.0
    
    async def _calculate_formatting_score(self, original: str, translated: str) -> float:
        """Calculate formatting preservation score"""
        try:
            # Check for preservation of basic formatting elements
            
            # Paragraph breaks
            original_paragraphs = original.count('\n\n')
            translated_paragraphs = translated.count('\n\n')
            paragraph_score = 1.0 - abs(original_paragraphs - translated_paragraphs) / max(1, original_paragraphs + 1)
            
            # Line breaks
            original_lines = original.count('\n')
            translated_lines = translated.count('\n')
            line_score = 1.0 - abs(original_lines - translated_lines) / max(1, original_lines + 1)
            
            # Punctuation preservation
            original_punct = len(re.findall(r'[.!?,:;]', original))
            translated_punct = len(re.findall(r'[.!?,:;]', translated))
            punct_score = 1.0 - abs(original_punct - translated_punct) / max(1, original_punct + 1)
            
            # Combine scores
            formatting_score = (paragraph_score * 0.4 + line_score * 0.3 + punct_score * 0.3)
            return min(1.0, max(0.0, formatting_score))
            
        except Exception as e:
            logger.error(f"Error calculating formatting score: {e}")
            return 0.0
    
    def _get_quality_level(self, score: float) -> str:
        """Convert numeric score to quality level"""
        if score >= 0.9:
            return "excellent"
        elif score >= 0.7:
            return "good"
        elif score >= 0.5:
            return "fair"
        else:
            return "poor"
    
    async def get_quality_trends(
        self, 
        document_id: int, 
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get quality trends over time for a document"""
        try:
            pages = self.db.query(PDFPage).filter(
                PDFPage.document_id == document_id
            ).order_by(PDFPage.page_number.asc()).all()
            
            trends = []
            cumulative_score = 0
            
            for i, page in enumerate(pages):
                if page.translated_text:
                    scores = await self.score_translation(
                        page.original_text, 
                        page.translated_text, 
                        user_id
                    )
                    
                    cumulative_score += scores["overall"]
                    average_score = cumulative_score / (i + 1)
                    
                    trends.append({
                        "page_number": page.page_number,
                        "page_score": scores["overall"],
                        "cumulative_average": round(average_score, 2),
                        "quality_level": scores["quality_level"]
                    })
            
            return {
                "document_id": document_id,
                "trends": trends,
                "overall_trend": "improving" if len(trends) > 1 and trends[-1]["cumulative_average"] > trends[0]["cumulative_average"] else "stable"
            }
            
        except Exception as e:
            logger.error(f"Error getting quality trends: {e}")
            return {
                "document_id": document_id,
                "trends": [],
                "error": str(e)
            }
