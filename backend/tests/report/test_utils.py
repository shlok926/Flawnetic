import pytest
from report.utils import (
    sanitize_text,
    sanitize_url,
    sanitize_steps,
    compute_risk_score,
    get_risk_label,
    format_code_snippet,
    truncate_text_smart,
    COLORS
)

def test_sanitize_text_unicode_replacements():
    raw_text = "Found — issue ‘quoted’ & “double” ✓ 🔴 €100"
    sanitized = sanitize_text(raw_text)
    assert "—" not in sanitized
    assert "Found - issue 'quoted' & \"double\" OK [CRITICAL] EUR100" == sanitized

def test_sanitize_text_none_and_truncation():
    assert sanitize_text(None) == ""
    long_text = "A" * 100
    truncated = sanitize_text(long_text, max_length=10)
    assert truncated == "AAAAAAA..."
    assert len(truncated) == 10

def test_sanitize_url():
    assert sanitize_url(None) == "N/A"
    assert sanitize_url("") == "N/A"
    short_url = "https://example.com/login"
    assert sanitize_url(short_url) == short_url
    long_url = "https://example.com/" + "a" * 100
    res = sanitize_url(long_url, max_length=30)
    assert res.endswith("...")
    assert len(res) == 30

def test_sanitize_steps_dict_and_list():
    assert sanitize_steps(None) == ["1. No reproduction steps recorded."]
    assert sanitize_steps([]) == ["1. No reproduction steps recorded."]

    dict_steps = {"step_1": "Navigate to /login", "step_2": "Enter payload <script>"}
    cleaned_dict = sanitize_steps(dict_steps)
    assert cleaned_dict == ["1. Navigate to /login", "2. Enter payload <script>"]

    list_dict_steps = [{"step": "1. Click submit"}, {"step": "step_2: Check result"}]
    cleaned_list_dict = sanitize_steps(list_dict_steps)
    assert cleaned_list_dict == ["1. Click submit", "2. Check result"]

    single_step = "1. Simple step text"
    cleaned_single = sanitize_steps(single_step)
    assert cleaned_single == ["1. Simple step text"]

def test_compute_risk_score():
    assert compute_risk_score([]) == 0.0
    findings = [
        {"severity": "CRITICAL"},
        {"severity": "HIGH"},
        {"severity": "MEDIUM"},
        {"severity": "LOW"}
    ]
    # Total weighted: 10 + 5 + 2 + 0.5 = 17.5. Max = 40. Score = (17.5/40)*10 = 4.375 -> 4.4
    score = compute_risk_score(findings)
    assert score == 4.4

def test_get_risk_label():
    assert get_risk_label(9.0) == ("CRITICAL RISK", COLORS["critical"])
    assert get_risk_label(7.0) == ("HIGH RISK", COLORS["high"])
    assert get_risk_label(5.0) == ("MEDIUM RISK", COLORS["medium"])
    assert get_risk_label(3.0) == ("LOW RISK", COLORS["low"])
    assert get_risk_label(1.0) == ("MINIMAL RISK", COLORS["success"])

def test_format_code_snippet():
    assert format_code_snippet(None) == "N/A"
    assert format_code_snippet("") == "N/A"
    snippet = "SELECT * FROM users WHERE id = '1' OR '1'='1'"
    assert format_code_snippet(snippet) == snippet
    long_snippet = "x" * 300
    res = format_code_snippet(long_snippet, max_length=50)
    assert res.endswith("...")
    assert len(res) == 53

def test_truncate_text_smart():
    assert truncate_text_smart(None) == ""
    text_with_period = "This is a first complete sentence. And here is second part that goes beyond."
    res = truncate_text_smart(text_with_period, limit=35)
    assert res == "This is a first complete sentence."

    text_no_period = "No sentence boundary here at all in this long string"
    res_no_period = truncate_text_smart(text_no_period, limit=20)
    assert res_no_period == "No sentence boundary..."
