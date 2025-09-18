from fastapi.testclient import TestClient


def test_chunked_flag_path(client: TestClient, monkeypatch):
    # Force chunking path
    from app.core import config as cfg
    old_flag = cfg.settings.USE_CHUNKING
    cfg.settings.USE_CHUNKING = True
    try:
        # Stub translator to avoid network and return deterministic result
        from app.services import translator as tr_module

        def fake_translate_page_chunked(self, db, page_id: int):
            from app.models.models import PDFPage
            page = db.query(PDFPage).filter(PDFPage.id == page_id).first()
            page.translated_text = "ترجمه آزمایشی"
            page.translation_status = "completed"
            page.cost_estimate = 0.001
            db.commit()
            return page

        monkeypatch.setattr(tr_module.Translator, "translate_page_chunked", fake_translate_page_chunked)

        # Upload a simple PDF (reuse existing unit helper by generating a tiny one)
        import io
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        c.drawString(72, 720, "Chunked Flag Test")
        c.showPage(); c.save()

        r = client.post("/api/documents/upload", files={"file": ("cflag.pdf", buf.getvalue(), "application/pdf")})
        assert r.status_code == 200, r.text
        doc_id = r.json()["document_id"]

        r2 = client.post(f"/api/documents/{doc_id}/pages/1/test")
        assert r2.status_code == 200, r2.text
        body = r2.json()
        assert body["translated_text"].strip()
    finally:
        cfg.settings.USE_CHUNKING = old_flag

