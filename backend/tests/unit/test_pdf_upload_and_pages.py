import io
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


def make_pdf_bytes(text: str = "Hello PDF") -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    width, height = letter
    c.drawString(72, height - 72, text)
    c.showPage()
    c.save()
    return buf.getvalue()


def test_upload_then_get_document_and_pages(client: TestClient):
    # Create a small one-page PDF in-memory
    pdf_bytes = make_pdf_bytes("Test Document for Upload")

    files = {"file": ("test.pdf", pdf_bytes, "application/pdf")}
    r = client.post("/api/documents/upload", files=files)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "document_id" in data and data["document_id"] > 0
    assert data["uuid"]
    assert data["total_pages"] >= 1
    doc_id = data["document_id"]

    # Fetch document
    r_doc = client.get(f"/api/documents/{doc_id}")
    assert r_doc.status_code == 200
    doc = r_doc.json()
    assert doc["id"] == doc_id
    assert doc["status"] in {"uploaded", "extracted"}
    assert doc["total_pages"] >= 1

    # Fetch pages list
    r_pages = client.get(f"/api/documents/{doc_id}/pages")
    assert r_pages.status_code == 200
    pages = r_pages.json()
    assert isinstance(pages, list) and len(pages) >= 1
    assert pages[0]["page_number"] == 1
    assert "translation_status" in pages[0]

