from dataclasses import dataclass

from app.services.translator import Translator


@dataclass
class FakeRes:
    text: str
    prompt_tokens: int = 10
    completion_tokens: int = 20


class FakeLLM:
    def __init__(self):
        self.calls = 0

    def chat(self, system: str, user: str, *, temperature: float = 0.1, max_tokens: int = 800):
        self.calls += 1
        assert system and user
        return FakeRes(text="ترجمه")


def test_translator_uses_chunker_and_llm(monkeypatch):
    llm = FakeLLM()
    tr = Translator(llm=llm, chunk_tokens=200)
    res = tr.translate_text("Paragraph A.\n\nParagraph B.")
    assert isinstance(res, dict)
    assert res["text"].strip()
    assert res["prompt_tokens"] >= 10
    assert res["completion_tokens"] >= 20
    assert llm.calls >= 1

