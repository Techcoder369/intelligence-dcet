import re

KEY_PATTERNS = [
    r"\bis defined as\b",
    r"\brefers to\b",
    r"\bmeans\b",
    r"\bis called\b",
    r"\bis the process of\b",
    r"\bis a form\b",
    r"\bis used for\b",
]

def is_valid_concept(text: str) -> bool:
    text = text.lower()

    if len(text) < 50:
        return False

    for p in KEY_PATTERNS:
        if re.search(p, text):
            return True

    return False
