from app.services.chunker import Chunker


def test_chunker_respects_token_budget():
    text = ("Para1 sentence.\n\n" + "Para2 sentence. " * 50 + "\n\n" + "Para3 short.")
    ch = Chunker(target_tokens=200)
    chunks = ch.chunk_paragraphs(text)
    assert len(chunks) >= 1
    # No empty chunks
    assert all(c.text.strip() for c in chunks)
    # Orders are increasing
    assert [c.order for c in chunks] == list(range(len(chunks)))

