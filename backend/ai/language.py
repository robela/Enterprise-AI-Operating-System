"""Language helpers for multilingual chat and RAG (no LLM calls)."""
from __future__ import annotations

import re
import unicodedata

# Display names used in prompts. Codes not listed here are passed to the model as-is.
LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "am": "Amharic",
    "om": "Afaan Oromo",
    "ti": "Tigrinya",
    "so": "Somali",
    "aa": "Afar",
    "sw": "Swahili",
    "ny": "Chichewa",
    "fr": "French",
    "ar": "Arabic",
    "es": "Spanish",
    "pt": "Portuguese",
}

# Languages whose script differs from Latin, so an answer in the wrong language can be
# detected by script alone. Latin-script languages (English, Oromo, Somali...) cannot.
LANGUAGE_SCRIPTS: dict[str, str] = {
    "am": "ethiopic",
    "ti": "ethiopic",
    "ar": "arabic",
    "fa": "arabic",
    "ur": "arabic",
    "hi": "devanagari",
    "ru": "cyrillic",
    "uk": "cyrillic",
    "zh": "cjk",
    "ko": "hangul",
}

_CODE_RE = re.compile(r"^[a-z]{2,3}(?:-[a-z0-9]{2,8})*$")
_NAME_TO_CODE = {name.casefold(): code for code, name in LANGUAGE_NAMES.items()}
_NAME_TO_CODE.update({"oromo": "om", "afan oromo": "om", "oromiffa": "om"})


def normalize_language_code(value: object) -> str | None:
    """Return a lowercase language tag such as "am" or "pt-br", or None if invalid."""
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    by_name = _NAME_TO_CODE.get(raw.casefold())
    if by_name:
        return by_name
    code = raw.lower().replace("_", "-")
    if code in ("und", "unknown", "zxx"):
        return None
    return code if _CODE_RE.match(code) else None


def base_language(code: str | None) -> str | None:
    """"am-ET" -> "am"."""
    return code.split("-", 1)[0] if code else None


def language_name(code: str | None) -> str:
    base = base_language(code)
    return LANGUAGE_NAMES.get(base or "", code or "the user's language")


def script_counts(text: str) -> dict[str, int]:
    """Count letters per Unicode script ("latin", "ethiopic", ...)."""
    counts: dict[str, int] = {}
    for ch in text:
        if not ch.isalpha():
            continue
        name = unicodedata.name(ch, "")
        script = name.split(" ", 1)[0].lower() if name else "unknown"
        counts[script] = counts.get(script, 0) + 1
    return counts


def dominant_script(text: str) -> str | None:
    counts = script_counts(text)
    return max(counts, key=counts.__getitem__) if counts else None


def expected_script(language: str | None, question: str = "") -> str | None:
    """Script the answer should be written in, when it can be checked.

    Uses the language when it has a distinctive script. When the language is unknown,
    falls back to the question's script if it is not Latin (e.g. an Ethiopic question).
    """
    if language:
        return LANGUAGE_SCRIPTS.get(base_language(language) or "")
    script = dominant_script(question)
    return script if script and script != "latin" else None


def answer_matches_language(
    answer: str, language: str | None, question: str = "", min_share: float = 0.2
) -> bool:
    """False only when the answer is clearly in the wrong script (e.g. English for Amharic)."""
    script = expected_script(language, question)
    if not script:
        return True
    counts = script_counts(answer)
    total = sum(counts.values())
    if total < 8:
        return True
    return counts.get(script, 0) / total >= min_share


def language_directive(language: str | None) -> str:
    """Instruction appended to system prompts so answers come back in the right language."""
    if language:
        name = language_name(language)
        return f"Response language: {name} ({language}). Write the entire answer in {name}."
    return "Response language: the same language as the user's question."


def rewrite_instruction(language: str | None) -> str:
    target = language_name(language) if language else "the same language as my question"
    return (
        f"Rewrite your previous answer in {target}. Keep the same facts, numbers, "
        "and [Source: ...] citations."
    )
