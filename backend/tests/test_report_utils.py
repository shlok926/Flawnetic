import pytest
from report.utils import sanitize_text, sanitize_steps, compute_risk_score

def test_sanitize_text_basic():
    raw_text = "System error with \u201dsmart quotes\u201d & special chars"
    sanitized = sanitize_text(raw_text)
    assert isinstance(sanitized, str)
    assert "\u201d" not in sanitized
    assert "smart quotes" in sanitized

def test_sanitize_text_truncation():
    long_text = "A" * 1000
    sanitized = sanitize_text(long_text, max_length=500)
    assert len(sanitized) <= 500

def test_sanitize_steps_string():
    raw_steps = "Navigate to /login"
    steps = sanitize_steps(raw_steps)
    assert isinstance(steps, list)
    assert len(steps) == 1
    assert "1. Navigate to /login" in steps[0]

def test_sanitize_steps_list():
    raw_list = ["Step 1: Open URL", "Step 2: Click submit"]
    steps = sanitize_steps(raw_list)
    assert isinstance(steps, list)
    assert len(steps) == 2

def test_compute_risk_score_empty():
    score = compute_risk_score([])
    assert score == 0.0

def test_compute_risk_score_high_critical():
    findings = [
        {"severity": "CRITICAL"}, # 10.0
        {"severity": "HIGH"},     # 5.0
        {"severity": "MEDIUM"},   # 2.0
        {"severity": "LOW"}       # 0.5
    ]
    score = compute_risk_score(findings)
    assert 0.0 <= score <= 10.0
    assert score > 3.0
