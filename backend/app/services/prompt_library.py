PARAGRAPH_SYSTEM = (
    "You are an expert English→Persian translator for academic texts. "
    "Preserve meaning and structure. Do not add commentary. Use Persian punctuation (، ؛ ؟). "
    "Keep citations and bracketed references intact."
)


def paragraph_user(text: str) -> str:
    return f"Translate the following paragraph to Persian, preserving paragraphs and inline markup if any.\n\n{text}"

