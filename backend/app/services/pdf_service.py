import fitz
import os
from sqlalchemy.orm import Session
from app.models.enhanced_models import PDFDocument, PDFPage
from app.core.config import settings
from typing import List, Dict
import json
from datetime import datetime

class PDFService:
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> List[Dict]:
        """Extract text from PDF with page information"""
        doc = fitz.open(file_path)
        pages = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            
            pages.append({
                'page_number': page_num + 1,
                'text': text,
                'char_count': len(text)
            })
        
        doc.close()
        return pages

    @staticmethod
    def save_pdf_to_db(db: Session, filename: str, original_filename: str, file_path: str) -> PDFDocument:
        """Save PDF document to database"""
        # Extract basic info first
        doc = fitz.open(file_path)
        total_pages = len(doc)
        doc.close()
        
        pdf_doc = PDFDocument(
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            total_pages=total_pages,
            status="uploaded"
        )
        
        db.add(pdf_doc)
        db.commit()
        db.refresh(pdf_doc)
        return pdf_doc

    @staticmethod
    def extract_and_save_pages(db: Session, document_id: int, file_path: str):
        """Extract text and save pages to database"""
        pages = PDFService.extract_text_from_pdf(file_path)
        total_chars = 0
        
        for page_data in pages:
            page = PDFPage(
                document_id=document_id,
                page_number=page_data['page_number'],
                original_text=page_data['text'],
                char_count=page_data['char_count'],
                translation_status="pending"
            )
            total_chars += page_data['char_count']
            db.add(page)
        
        # Update document with total characters
        document = db.query(PDFDocument).filter(PDFDocument.id == document_id).first()
        if document:
            document.total_characters = total_chars
            document.status = "extracted"
            db.commit()
        
        return len(pages)

    @staticmethod
    def mark_page_as_test(db: Session, document_id: int, page_number: int) -> PDFPage:
        """Mark a page as test page for translation"""
        page = db.query(PDFPage).filter(
            PDFPage.document_id == document_id,
            PDFPage.page_number == page_number
        ).first()
        
        if page:
            page.is_test_page = True
            db.commit()
            db.refresh(page)
        
        return page
