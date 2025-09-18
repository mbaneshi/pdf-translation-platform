from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io


def make_pdf_bytes(text: str = "Start Translation Stub") -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(72, 720, text)
    c.showPage()
    c.save()
    return buf.getvalue()


def test_start_translation_uses_task_delay_stub(client: TestClient, monkeypatch):
    # Upload a PDF
    pdf_bytes = make_pdf_bytes()
    r = client.post("/api/documents/upload", files={"file": ("start.pdf", pdf_bytes, "application/pdf")})
    assert r.status_code == 200
    doc_id = r.json()["document_id"]

    # Stub the celery task's delay method
    from app.api.endpoints import documents as docs_module

    class FakeResult:
        def __init__(self, id):
            self.id = id

    def fake_delay(document_id: int):
        return FakeResult(id="task-123")

    # process_document_translation is a Celery task object; attach .delay
    task_obj = docs_module.process_document_translation
    monkeypatch.setattr(task_obj, "delay", fake_delay, raising=False)

    r2 = client.post(f"/api/documents/{doc_id}/translate")
    assert r2.status_code == 200, r2.text
    body = r2.json()
    assert body["message"].lower().startswith("translation started")
    assert body["task_id"] == "task-123"

