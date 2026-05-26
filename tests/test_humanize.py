from app.llm.humanize import sanitize_lead_message


def test_strips_extraction_block():
    raw = "Hi John!\n\n<<<EXTRACTED>>>\n{}\n<<<END>>>"
    assert "<<<" not in sanitize_lead_message(raw)


def test_removes_ai_phrasing():
    raw = "I'm an AI assistant for Reva. How can I help?"
    out = sanitize_lead_message(raw)
    assert "AI" not in out
    assert "Reva" not in out
