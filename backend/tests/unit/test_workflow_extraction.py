from backend.ai.graph.workflow_extraction import extract_workflow_drafts


def test_extract_workflow_drafts_groups_same_page_instructions() -> None:
    drafts = extract_workflow_drafts(
        [
            "Ask the child's age. Check for general danger signs. "
            "Ask about main symptoms. Check nutrition and immunization status.",
        ]
    )

    assert len(drafts) == 1
    assert drafts[0].source_pages == [1]
    assert drafts[0].required_fields == [
        "child_age",
        "general_danger_signs",
        "main_symptoms",
        "nutrition_status",
        "immunization_status",
    ]
    assert len(drafts[0].steps) == 4


def test_extract_workflow_drafts_skips_single_instruction_pages() -> None:
    assert extract_workflow_drafts(["Ask the child's age."]) == []