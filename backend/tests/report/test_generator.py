import pytest
from unittest.mock import MagicMock, patch
from report.generator import PDFReportGenerator, FlawneticPDF

def test_flawnetic_pdf_safe_cell_ln_zero():
    pdf = FlawneticPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=10)
    pdf.safe_cell(w=50, h=10, txt="Inline cell text", ln=0, align="L")
    assert pdf.get_x() > 10

def test_pdf_report_generator_s3_init_exception():
    with patch("report.generator.boto3.client", side_effect=Exception("AWS connection error")):
        generator = PDFReportGenerator()
        assert generator.s3_client is None

def test_pdf_report_generator_ensure_bucket_exists_exception():
    mock_s3 = MagicMock()
    mock_s3.head_bucket.side_effect = Exception("Bucket not found")
    mock_s3.create_bucket.side_effect = Exception("Permission denied")

    with patch("report.generator.boto3.client", return_value=mock_s3):
        generator = PDFReportGenerator()
        assert generator.s3_client == mock_s3

@patch("report.generator.boto3.client")
def test_generate_pdf_bytes_empty_findings(mock_boto):
    generator = PDFReportGenerator()
    pdf_bytes = generator._generate_pdf_bytes(
        scan_run_id="scan-empty",
        findings=[],
        project_name="Clean App",
        target_url="https://example.com",
        total_pages=5
    )
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0

@patch("report.generator.boto3.client")
def test_generate_pdf_bytes_with_ai_root_cause_hint(mock_boto):
    generator = PDFReportGenerator()
    findings = [{
        "bug_id": "FL-001",
        "title": "SQL Injection",
        "severity": "CRITICAL",
        "module": "security",
        "page_url": "https://example.com/search",
        "description": "SQL Injection vulnerability in search parameter.",
        "steps_to_reproduce": {"step1": "Enter ' OR 1=1--"},
        "payload": "' OR 1=1--",
        "expected_result": "Input sanitized.",
        "actual_result": "Database error returned.",
        "root_cause_hint": "Use parameterized queries in SQLAlchemy."
    }]

    pdf_bytes = generator._generate_pdf_bytes(
        scan_run_id="scan-ai",
        findings=findings,
        project_name="Vulnerable App",
        target_url="https://example.com",
        total_pages=2
    )
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0

def test_upload_to_minio_s3_failure_local_fallback():
    mock_s3 = MagicMock()
    mock_s3.put_object.side_effect = Exception("S3 bucket write failed")

    with patch("report.generator.boto3.client", return_value=mock_s3):
        generator = PDFReportGenerator()
        url = generator._upload_to_minio(b"%PDF-test", "scan-fallback-1")
        assert url is not None
        assert "scan-fallback-1.pdf" in url

@patch("report.generator.boto3.client")
def test_generate_and_upload_pdf_generation_exception(mock_boto):
    generator = PDFReportGenerator()
    with patch.object(generator, "_generate_pdf_bytes", side_effect=RuntimeError("PDF render crash")):
        res = generator.generate_and_upload(
            scan_run_id="scan-crash",
            findings=[],
            project_name="Crash App",
            target_url="https://example.com"
        )
        assert res is None
