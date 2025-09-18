import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from app.services.pdf_service import PDFService
from app.services.persian_text_processor import PersianTextProcessor
from app.services.semantic_analyzer import SemanticAnalyzer
from app.services.translation_service import TranslationService
from app.services import translation_service as ts_module


def make_pdf_file(tmp_path, text: str = "Coverage PDF") -> str:
    p = tmp_path / "cov.pdf"
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(72, 720, text + " | A | B | C")
    c.showPage()
    c.save()
    p.write_bytes(buf.getvalue())
    return str(p)


def test_pdf_service_extract_text(tmp_path):
    path = make_pdf_file(tmp_path)
    pages = PDFService.extract_text_from_pdf(path)
    assert isinstance(pages, list) and len(pages) == 1
    assert pages[0]["page_number"] == 1
    assert pages[0]["char_count"] > 0


def test_persian_text_processor_basic():
    ptp = PersianTextProcessor()
    # Check punctuation conversion and RTL processing path
    out = ptp.format_persian_text("Hello?", preserve_spacing=True)
    assert isinstance(out, str)
    # Validate helper methods
    validation = ptp.validate_persian_translation("Hello.", "سلام.")
    assert "quality_score" in validation


def test_semantic_analyzer_on_pdf(tmp_path):
    path = make_pdf_file(tmp_path)
    analyzer = SemanticAnalyzer()
    structures = analyzer.analyze_document_structure(path)
    assert isinstance(structures, dict)
    assert set(["sentences", "paragraphs", "sections", "chapters", "tables", "columns"]).issubset(structures.keys())


def test_translation_service_non_network(monkeypatch):
    # Avoid real tiktoken; provide a lightweight stub
    class DummyTok:
        def encode(self, text: str):
            return list(text.encode("utf-8"))

    monkeypatch.setattr(ts_module.tiktoken, "get_encoding", lambda name: DummyTok())

    ts = TranslationService()
    # Only test local helpers to avoid network: estimate + stats
    est = ts.estimate_cost("Short text for estimate.")
    assert est >= 0
    stats = ts.get_translation_statistics("Short text for stats.")
    assert stats["char_count"] > 0 and stats["token_count"] >= 0
