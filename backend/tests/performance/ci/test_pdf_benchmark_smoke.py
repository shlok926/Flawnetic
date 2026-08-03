import pytest
import time
import statistics
from unittest.mock import patch

from report.generator import PDFReportGenerator

@patch("report.generator.boto3.client")
def test_pdf_generation_latency_benchmark(mock_boto):
    generator = PDFReportGenerator()

    sample_findings = [
        {
            "bug_id": f"FL-{i:03d}",
            "title": f"Vulnerability {i}",
            "severity": "HIGH",
            "module": "security",
            "page_url": f"https://example.com/page{i}",
            "description": f"Detailed description for issue {i}",
            "steps_to_reproduce": {"step1": "Reproduce step 1"},
            "expected_result": "Clean response",
            "actual_result": "Error code returned",
            "root_cause_hint": "Sanitize user input"
        }
        for i in range(1, 10)
    ]

    # Warm-up (3 runs)
    for _ in range(3):
        generator._generate_pdf_bytes("scan-warmup", sample_findings, "Test Proj", "https://example.com", 5)

    durations = []
    for i in range(10):
        start = time.perf_counter()
        pdf_bytes = generator._generate_pdf_bytes(f"scan-bench-{i}", sample_findings, "Test Proj", "https://example.com", 5)
        elapsed = time.perf_counter() - start
        assert len(pdf_bytes) > 0
        durations.append(elapsed)

    durations.sort()
    p95 = durations[int(len(durations) * 0.95)]
    p50 = statistics.median(durations)

    # Budget: PDF Generation <= 5.0 seconds
    assert p95 <= 5.0, f"PDF Generation P95 latency exceeded budget: {p95:.2f}s > 5.0s"
