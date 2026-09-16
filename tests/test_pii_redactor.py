from app.services.pii_redactor import redact_text


def test_selected_pii_is_replaced() -> None:
    text = (
        "Contact Alex Morgan at alex.morgan@example.test or "
        "+1 202-555-0147. The test server is 192.0.2.25."
    )

    sanitized, counts = redact_text(text)

    assert "alex.morgan@example.test" not in sanitized
    assert "192.0.2.25" not in sanitized
    assert "<EMAIL_ADDRESS>" in sanitized
    assert "<IP_ADDRESS>" in sanitized
    assert counts["EMAIL_ADDRESS"] >= 1
    assert counts["IP_ADDRESS"] >= 1


def test_empty_text_is_unchanged() -> None:
    sanitized, counts = redact_text("")
    assert sanitized == ""
    assert sum(counts.values()) == 0
