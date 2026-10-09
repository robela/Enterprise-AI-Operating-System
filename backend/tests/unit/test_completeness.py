from backend.ai.graph.completeness import extract_requirement_candidates


def test_extract_requirement_candidates_keeps_pdf_page_evidence() -> None:
    candidates = extract_requirement_candidates(
        [
            "The handbook explains how to assess sick children. Assess the child's ability to drink.",
            "Measure the child's temperature. Introduction to the guideline.",
        ]
    )

    assert [(candidate.text, candidate.page_number) for candidate in candidates] == [
        ("Assess the child's ability to drink.", 1),
        ("Measure the child's temperature.", 2),
    ]


def test_extract_requirement_candidates_deduplicates_and_respects_limit() -> None:
    candidates = extract_requirement_candidates(
        ["Check for danger signs. Check for danger signs. Ask about the duration."],
        limit=1,
    )

    assert [(candidate.text, candidate.page_number) for candidate in candidates] == [
        ("Check for danger signs.", 1),
    ]