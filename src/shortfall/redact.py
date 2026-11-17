import re

MASK = "[masked key]"
PATTERNS = (
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{8,}"),
    re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"(?<=ANTHROPIC_API_KEY=)[^\s\"'\\]+"),
)

_known: set[str] = set()


def register(value: str) -> None:
    if value and len(value) >= 8:
        _known.add(value)


def mask(text: str) -> str:
    for value in sorted(_known, key=len, reverse=True):
        text = text.replace(value, MASK)
    for pattern in PATTERNS:
        text = pattern.sub(MASK, text)
    return text
