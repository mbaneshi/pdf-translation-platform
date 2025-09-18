from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io


def make_pdf_bytes(text: str = "Page Translate Test") -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(72, 720, text)
    c.showPage()
    c.save()
    return buf.getvalue()


def test_test_translate_page_with_mocks(client: TestClient, monkeypatch):
    # Mock TranslationService to avoid external API
    from app.services import translation_service as ts_module

    def fake_translate_text(self, text: str, max_retries: int = 3) -> str:
        return "ترجمه آزمایشی"

    def fake_estimate_cost(self, text: str) -> float:
        return 0.01

    monkeypatch.setattr(ts_module.TranslationService, "translate_text", fake_translate_text)
    monkeypatch.setattr(ts_module.TranslationService, "estimate_cost", fake_estimate_cost)

    # Upload a PDF
    pdf_bytes = make_pdf_bytes()
    r = client.post("/api/documents/upload", files={"file": ("sample.pdf", pdf_bytes, "application/pdf")})
    assert r.status_code == 200
    doc_id = r.json()["document_id"]

    # Trigger test translation for page 1
    r2 = client.post(f"/api/documents/{doc_id}/pages/1/test")
    assert r2.status_code == 200, r2.text
    body = r2.json()
    assert body["message"].lower().startswith("test page translated")
    assert body["page_number"] == 1
    assert isinstance(body["translated_text"], str) and body["translated_text"]

