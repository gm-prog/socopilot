"""Unit tests for app.middleware.pii_redaction — pure redact_pii function."""

from app.middleware.pii_redaction import redact_pii


def test_redact_email():
    assert redact_pii("Contact admin@example.com for help") == (
        "Contact [REDACTED_EMAIL] for help"
    )


def test_redact_multiple_emails():
    text = "From a@b.com to c@d.org"
    result = redact_pii(text)
    assert result.count("[REDACTED_EMAIL]") == 2


def test_redact_ssn():
    assert "[REDACTED_SSN]" in redact_pii("SSN 123-45-6789 on file")


def test_redact_ip():
    assert "[REDACTED_IP]" in redact_pii("Source IP 192.168.1.100 detected")


def test_redact_phone():
    result = redact_pii("Call 555-123-4567 now")
    assert "[REDACTED_PHONE]" in result


def test_no_pii_unchanged():
    safe = "No sensitive data here"
    assert redact_pii(safe) == safe


def test_redact_multiple_types():
    text = "User admin@corp.com from 10.0.0.1 SSN 111-22-3333"
    result = redact_pii(text)
    assert "[REDACTED_EMAIL]" in result
    assert "[REDACTED_IP]" in result
    assert "[REDACTED_SSN]" in result


def test_empty_string():
    assert redact_pii("") == ""
