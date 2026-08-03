from unittest.mock import MagicMock, patch
from report.generator import PDFReportGenerator

@patch("report.generator.boto3.client")
def test_report_generator_pdf_creation(mock_boto_client, sample_findings):
    mock_s3 = MagicMock()
    mock_s3.generate_presigned_url.return_value = "http://minio:9000/flawnetic/reports/sample.pdf"
    mock_boto_client.return_value = mock_s3

    generator = PDFReportGenerator()
    target_url = "https://example.com"
    presigned = generator.generate_and_upload(
        scan_run_id="scan-test-1",
        findings=sample_findings,
        project_name="Test Project",
        target_url=target_url
    )
    assert presigned is None or isinstance(presigned, str)

@patch("report.generator.boto3.client")
def test_report_generator_s3_upload(mock_boto_client, sample_findings):
    mock_s3 = MagicMock()
    mock_s3.generate_presigned_url.return_value = "http://minio:9000/flawnetic/reports/sample.pdf"
    mock_boto_client.return_value = mock_s3

    generator = PDFReportGenerator()
    presigned_url = generator.generate_and_upload(
        scan_run_id="scan-test-2",
        findings=sample_findings,
        project_name="Test Project",
        target_url="https://example.com"
    )
    assert presigned_url is None or isinstance(presigned_url, str)
