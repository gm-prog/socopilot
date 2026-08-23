"""LLM Prompt Injection Defense and Input Sanitization Utilities."""

import re
from typing import Any

INJECTION_PATTERNS = [
    re.compile(r"\b(ignore\s+(all\s+)?previous\s+instructions?)\b", re.IGNORECASE),
    re.compile(r"\b(disregard\s+(all\s+)?prior\s+prompts?)\b", re.IGNORECASE),
    re.compile(r"\b(system\s+prompt|system\s+override)\b", re.IGNORECASE),
    re.compile(r"<\|im_start\|>|<\|im_end\|>|<\|endoftext\|>", re.IGNORECASE),
    re.compile(r"\b(you\s+are\s+now\s+a|act\s+as\s+a)\b", re.IGNORECASE),
]


def sanitize_input_text(text: str) -> str:
    """
    Sanitizes raw text to prevent prompt injection.
    - Redacts malicious override phrases
    - Escapes XML tags that could break prompt structure
    """
    if not text:
        return ""

    sanitized = text
    for pattern in INJECTION_PATTERNS:
        sanitized = pattern.sub("[REDACTED_PROMPT_INJECTION]", sanitized)

    # Escape XML delimiters if present in untrusted payload
    sanitized = sanitized.replace("<untrusted_content>", "&lt;untrusted_content&gt;")
    sanitized = sanitized.replace("</untrusted_content>", "&lt;/untrusted_content&gt;")

    return sanitized


def wrap_untrusted_payload(payload: Any) -> str:
    """
    Converts payload to string and encapsulates it in untrusted XML delimiters.
    """
    import json

    if isinstance(payload, (dict, list)):
        raw_str = json.dumps(payload, default=str)
    else:
        raw_str = str(payload)

    clean_str = sanitize_input_text(raw_str)
    return f"<untrusted_content>\n{clean_str}\n</untrusted_content>"
