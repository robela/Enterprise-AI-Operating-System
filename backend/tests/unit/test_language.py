"""Unit tests for language helpers."""
from backend.ai.language import (
    answer_matches_language,
    dominant_script,
    language_directive,
    language_name,
    normalize_language_code,
)

AMHARIC_TEXT = "መመሪያው በገጽ አራት ላይ ነው።"
ENGLISH_TEXT = "The guideline is on page four of the manual."


def test_normalize_language_code_accepts_codes_and_names() -> None:
    assert normalize_language_code("am") == "am"
    assert normalize_language_code(" AM ") == "am"
    assert normalize_language_code("pt_BR") == "pt-br"
    assert normalize_language_code("Amharic") == "am"
    assert normalize_language_code("Afaan Oromo") == "om"
    assert normalize_language_code("Oromo") == "om"


def test_normalize_language_code_rejects_unknown_values() -> None:
    assert normalize_language_code(None) is None
    assert normalize_language_code("") is None
    assert normalize_language_code("und") is None
    assert normalize_language_code("not a language code") is None
    assert normalize_language_code(42) is None


def test_language_name_falls_back_to_code() -> None:
    assert language_name("om") == "Afaan Oromo"
    assert language_name("am-ET") == "Amharic"
    assert language_name("kri") == "kri"


def test_dominant_script() -> None:
    assert dominant_script(AMHARIC_TEXT) == "ethiopic"
    assert dominant_script(ENGLISH_TEXT) == "latin"
    assert dominant_script("123 !?") is None


def test_english_answer_for_amharic_is_a_mismatch() -> None:
    assert answer_matches_language(ENGLISH_TEXT, "am") is False
    assert answer_matches_language(AMHARIC_TEXT, "am") is True


def test_amharic_answer_with_english_citation_still_matches() -> None:
    answer = f"{AMHARIC_TEXT} [Source: guideline-2024]"
    assert answer_matches_language(answer, "am") is True


def test_latin_script_languages_are_not_checked() -> None:
    # Oromo and English share the Latin script, so the check cannot tell them apart.
    assert answer_matches_language(ENGLISH_TEXT, "om") is True


def test_unknown_language_uses_question_script() -> None:
    assert answer_matches_language(ENGLISH_TEXT, None, question=AMHARIC_TEXT) is False
    assert answer_matches_language(ENGLISH_TEXT, None, question=ENGLISH_TEXT) is True


def test_short_answers_are_not_judged() -> None:
    assert answer_matches_language("OK", "am") is True


def test_language_directive() -> None:
    assert "Amharic (am)" in language_directive("am")
    assert "same language as the user's question" in language_directive(None)
