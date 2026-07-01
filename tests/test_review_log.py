from pathlib import Path


def test_security_review_log_records_webapp_and_history_dispositions():
    review_log = Path("docs/review-log.md")

    assert review_log.exists()
    text = review_log.read_text()
    assert "webapp DOM XSS" in text
    assert "c06bccdce17001b1f0e36144b6c7beefd69ddcb1" in text
    assert "owner-gated" in text
