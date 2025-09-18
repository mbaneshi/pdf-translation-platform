from fastapi.testclient import TestClient


def test_translation_progress_rollups(client: TestClient, monkeypatch):
    # Enable chunked path
    from app.core import config as cfg
    old_flag = cfg.settings.USE_CHUNKING
    cfg.settings.USE_CHUNKING = True
    try:
        # Stub translator to set tokens & cost
        from app.services import translator as tr_module

        def fake_translate_page_chunked(self, db, page_id: int):
            from app.models.models import PDFPage
            p = db.query(PDFPage).filter(PDFPage.id == page_id).first()
            p.translated_text = "خروجی"
            p.translation_status = "completed"
            p.cost_estimate = 0.002
            p.tokens_in = 111
            p.tokens_out = 222
            db.commit()
            return p

        monkeypatch.setattr(tr_module.Translator, "translate_page_chunked", fake_translate_page_chunked)

        # Create a simple one-page PDF
        import io
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=letter)
        c.drawString(72, 720, "Progress Test")
        c.showPage(); c.save()

        r = client.post("/api/documents/upload", files={"file": ("p.pdf", buf.getvalue(), "application/pdf")})
        assert r.status_code == 200
        doc_id = r.json()["document_id"]

        # Create a job
        rj = client.post(f"/api/enhanced/gradual-translate/{doc_id}")
        assert rj.status_code == 200

        # Sample translate page 1 to trigger tokens/cost
        rs = client.post(f"/api/enhanced/translate-sample/{doc_id}/page/1")
        assert rs.status_code == 200

        # Query progress with rollups
        rp = client.get(f"/api/enhanced/translation-progress/{doc_id}")
        assert rp.status_code == 200
        body = rp.json()
        assert "tokens_in_total" in body and body["tokens_in_total"] >= 111
        assert "tokens_out_total" in body and body["tokens_out_total"] >= 222
        assert "pages_cost_total" in body and body["pages_cost_total"] >= 0.002
    finally:
        cfg.settings.USE_CHUNKING = old_flag

