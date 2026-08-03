import pytest
from triage.engine import AITriageEngine

def test_triage_engine_initialization():
    engine = AITriageEngine()
    assert engine is not None

def test_triage_deduplication(sample_findings):
    engine = AITriageEngine()
    # Duplicate findings
    findings = sample_findings + sample_findings
    triaged = engine.triage(findings)
    assert len(triaged) <= len(findings)
    assert any(f.get("bug_id") for f in triaged)

def test_triage_severity_normalization():
    engine = AITriageEngine()
    raw_findings = [
        {"title": "Possible SQL Injection Vulnerability", "module": "security", "page_url": "https://example.com/login"},
        {"title": "Missing CSP Header", "module": "security", "page_url": "https://example.com/"}
    ]
    triaged = engine.triage(raw_findings)
    assert len(triaged) == 2
    assert triaged[0]["severity"] == "critical"
    assert triaged[1]["severity"] == "high"
