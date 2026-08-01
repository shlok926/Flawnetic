"""
report/generator.py
-------------------
PDF report generator for Flawnetic scan results.

Design decisions:
- FPDF2 chosen over WeasyPrint: WeasyPrint requires GTK which is not
  available on Windows without manual installation. FPDF2 is pure Python
  and works cross-platform.
- All strings sanitized via report/utils.py before rendering.
- MinIO upload failure is non-fatal: local fallback path returned.
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

import boto3
from fpdf import FPDF
from config.settings import settings
from report.utils import sanitize_text, sanitize_url, sanitize_steps

logger = logging.getLogger(__name__)


class FlawneticPDF(FPDF):
    """FPDF subclass providing safe cell rendering methods."""

    def safe_cell(self, w=0, h=0, txt="", border=0, ln=0, align="", fill=False, link="", max_length=None):
        clean_txt = sanitize_text(txt, max_length=max_length)
        effective_w = self.epw if w == 0 else w
        if ln != 0:
            self.cell(effective_w, h, clean_txt, border=border, new_x="LMARGIN", new_y="NEXT", align=align, fill=fill, link=link)
        else:
            self.cell(effective_w, h, clean_txt, border=border, align=align, fill=fill, link=link)

    def safe_multi_cell(self, w=0, h=0, txt="", border=0, align="J", fill=False, max_length=None):
        clean_txt = sanitize_text(txt, max_length=max_length)
        effective_w = self.epw if w == 0 else w
        self.multi_cell(effective_w, h, clean_txt, border=border, align=align, fill=fill)


class PDFReportGenerator:
    """PDF Report Generator using pure Python FPDF2 with MinIO S3 storage."""

    def __init__(self):
        self.s3_client = None
        self.bucket = getattr(settings, 's3_bucket_name', 'flawnetic-evidence')
        
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=settings.s3_endpoint_url,
                aws_access_key_id=settings.s3_access_key,
                aws_secret_access_key=settings.s3_secret_key,
                region_name=settings.s3_region
            )
            self._ensure_bucket_exists()
        except Exception as e:
            logger.warning(f"S3/MinIO client init warning (will use local fallback if needed): {e}")

    def _ensure_bucket_exists(self):
        if not self.s3_client:
            return
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
        except Exception:
            try:
                self.s3_client.create_bucket(Bucket=self.bucket)
            except Exception as e:
                logger.warning(f"S3 bucket creation check warning: {e}")

    def _generate_pdf_bytes(
        self,
        scan_run_id: str,
        findings: List[Dict[str, Any]],
        project_name: str,
        target_url: str,
        total_pages: int = 1
    ) -> bytes:
        """Renders complete PDF document into bytes buffer."""
        pdf = FlawneticPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        # -------------------------------------------------------------
        # PAGE 1: COVER PAGE
        # -------------------------------------------------------------
        pdf.add_page()
        pdf.set_font("Helvetica", 'B', 22)
        pdf.set_text_color(79, 70, 229)
        pdf.safe_cell(h=15, txt="FLAWNETIC QA REPORT", align='C', ln=1)
        
        pdf.set_font("Helvetica", '', 10)
        pdf.set_text_color(100, 116, 139)
        pdf.safe_cell(h=6, txt="Autonomous Enterprise E2E QA & Vulnerability Audit Platform", align='C', ln=1)
        pdf.ln(12)

        # Cover Metadata Box
        pdf.set_font("Helvetica", 'B', 12)
        pdf.set_text_color(15, 23, 42)
        pdf.safe_cell(h=8, txt=f"Project: {project_name}", ln=1)
        pdf.set_font("Helvetica", '', 10)
        pdf.safe_cell(h=6, txt=f"Target URL: {sanitize_url(target_url, max_length=100)}", ln=1)
        pdf.safe_cell(h=6, txt=f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}", ln=1)
        pdf.safe_cell(h=6, txt=f"Pages Crawled: {total_pages}", ln=1)
        pdf.safe_cell(h=6, txt=f"Total Findings: {len(findings)}", ln=1)
        pdf.safe_cell(h=6, txt=f"Scan Run ID: {scan_run_id}", ln=1)
        pdf.ln(15)

        # -------------------------------------------------------------
        # PAGE 2: SUMMARY BREAKDOWN
        # -------------------------------------------------------------
        pdf.add_page()
        pdf.set_font("Helvetica", 'B', 14)
        pdf.set_text_color(15, 23, 42)
        pdf.safe_cell(h=10, txt="Executive Summary & Severity Breakdown", ln=1)
        pdf.ln(4)

        critical_c = sum(1 for f in findings if str(f.get("severity", "")).upper() == "CRITICAL")
        high_c = sum(1 for f in findings if str(f.get("severity", "")).upper() == "HIGH")
        medium_c = sum(1 for f in findings if str(f.get("severity", "")).upper() == "MEDIUM")
        low_c = sum(1 for f in findings if str(f.get("severity", "")).upper() == "LOW")

        pdf.set_font("Helvetica", 'B', 10)
        pdf.safe_cell(h=8, txt="Severity Breakdown Table:", ln=1)
        pdf.set_font("Helvetica", '', 10)
        pdf.safe_cell(h=6, txt=f"  [CRITICAL] Critical Severity: {critical_c}", ln=1)
        pdf.safe_cell(h=6, txt=f"  [HIGH]     High Severity:     {high_c}", ln=1)
        pdf.safe_cell(h=6, txt=f"  [MEDIUM]   Medium Severity:   {medium_c}", ln=1)
        pdf.safe_cell(h=6, txt=f"  [LOW]      Low Severity:      {low_c}", ln=1)
        pdf.ln(10)

        # -------------------------------------------------------------
        # PAGES 3+: FINDINGS (One per page / section)
        # -------------------------------------------------------------
        pdf.set_font("Helvetica", 'B', 14)
        pdf.safe_cell(h=10, txt="Detailed Finding Analysis & Reproduction Steps", ln=1)
        pdf.ln(4)

        if not findings:
            pdf.set_font("Helvetica", 'I', 11)
            pdf.set_text_color(16, 185, 129)
            pdf.safe_cell(h=10, txt="No issues found - Clean Audit (0 Flaws Detected).", ln=1)
        else:
            for idx, f in enumerate(findings, 1):
                pdf.add_page()
                pdf.set_font("Helvetica", 'B', 12)
                pdf.set_text_color(15, 23, 42)
                
                bug_id = f.get('bug_id') or f"FL-{idx:03d}"
                title = f.get('title', 'Untitled Flaw')
                sev = str(f.get('severity', 'LOW')).upper()
                mod = str(f.get('module', 'functional')).upper()

                pdf.safe_cell(h=8, txt=f"{bug_id} - {title}", ln=1)

                pdf.set_font("Helvetica", '', 10)
                pdf.set_text_color(71, 85, 105)
                pdf.safe_cell(h=6, txt=f"Severity: {sev}  |  Module: {mod}", ln=1)
                pdf.safe_cell(h=6, txt=f"Page URL: {sanitize_url(f.get('page_url'))}", ln=1)
                pdf.ln(4)

                # Description
                pdf.set_font("Helvetica", 'B', 10)
                pdf.set_text_color(15, 23, 42)
                pdf.safe_cell(h=6, txt="Description:", ln=1)
                pdf.set_font("Helvetica", '', 10)
                pdf.set_text_color(51, 65, 85)
                desc = f.get('description', 'No detailed description provided.')
                pdf.safe_multi_cell(h=5, txt=desc, max_length=500)
                pdf.ln(4)

                # Steps to Reproduce
                pdf.set_font("Helvetica", 'B', 10)
                pdf.set_text_color(15, 23, 42)
                pdf.safe_cell(h=6, txt="Steps to Reproduce:", ln=1)
                pdf.set_font("Helvetica", '', 9)
                pdf.set_text_color(51, 65, 85)
                steps_list = sanitize_steps(f.get('steps_to_reproduce'))
                for step in steps_list:
                    pdf.safe_cell(h=5, txt=f"  * {step}", ln=1, max_length=150)
                pdf.ln(4)

                # Expected Result
                pdf.set_font("Helvetica", 'B', 10)
                pdf.set_text_color(15, 23, 42)
                pdf.safe_cell(h=6, txt="Expected Result:", ln=1)
                pdf.set_font("Helvetica", '', 9)
                pdf.set_text_color(51, 65, 85)
                exp = f.get('expected_result', 'System should validate input and process request securely without errors.')
                pdf.safe_multi_cell(h=5, txt=exp, max_length=300)
                pdf.ln(4)

                # Actual Result
                pdf.set_font("Helvetica", 'B', 10)
                pdf.set_text_color(15, 23, 42)
                pdf.safe_cell(h=6, txt="Actual Result:", ln=1)
                pdf.set_font("Helvetica", '', 9)
                pdf.set_text_color(51, 65, 85)
                act = f.get('actual_result', 'Anomalous behavior or unhandled exception observed during scan.')
                pdf.safe_multi_cell(h=5, txt=act, max_length=300)
                pdf.ln(4)

                # Root Cause Hint
                hint = f.get('root_cause_hint')
                if hint:
                    pdf.set_font("Helvetica", 'B', 10)
                    pdf.set_text_color(22, 101, 52)
                    pdf.safe_cell(h=6, txt="Root Cause & AI Remediation Hint:", ln=1)
                    pdf.set_font("Helvetica", 'I', 9)
                    pdf.safe_multi_cell(h=5, txt=hint, max_length=300)

        # -------------------------------------------------------------
        # FOOTER (Last page)
        # -------------------------------------------------------------
        pdf.set_y(-15)
        pdf.set_font("Helvetica", 'I', 8)
        pdf.set_text_color(148, 163, 184)
        pdf.safe_cell(h=10, txt=f"Generated by Flawnetic - Automated QA Platform | Scan ID: {scan_run_id}", align='C')

        # Output bytes buffer
        return bytes(pdf.output())

    def _upload_to_minio(self, pdf_bytes: bytes, scan_run_id: str) -> Optional[str]:
        """
        Upload PDF to MinIO. Returns accessible URL.
        Falls back to local file if MinIO unavailable.
        Never raises — returns None on complete failure.
        """
        pdf_file_name = f"report_{scan_run_id}.pdf"
        s3_key = f"reports/{scan_run_id}/{pdf_file_name}"

        # Try MinIO/S3 upload first
        if self.s3_client:
            try:
                self.s3_client.put_object(
                    Bucket=self.bucket,
                    Key=s3_key,
                    Body=pdf_bytes,
                    ContentType='application/pdf'
                )
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket, 'Key': s3_key},
                    ExpiresIn=604800 # 7 days
                )
                logger.info(f"PDF uploaded to MinIO: {url}")
                return url
            except Exception as e:
                logger.error(f"MinIO upload failed for scan {scan_run_id}: {e}", exc_info=True)

        # Fallback: Save PDF locally
        try:
            local_dir = Path(__file__).parent.parent / "reports"
            local_dir.mkdir(parents=True, exist_ok=True)
            local_path = local_dir / f"{scan_run_id}.pdf"
            local_path.write_bytes(pdf_bytes)
            logger.warning(f"PDF saved locally as fallback: {local_path}")
            return str(local_path)
        except Exception as local_err:
            logger.error(f"Local PDF save also failed: {local_err}", exc_info=True)
            return None

    def generate_and_upload(
        self,
        scan_run_id: str,
        findings: List[Dict[str, Any]],
        project_name: str,
        target_url: str,
        total_pages: int = 1
    ) -> Optional[str]:
        """Generates PDF report bytes and uploads to S3/MinIO with local fallback."""
        try:
            pdf_bytes = self._generate_pdf_bytes(
                scan_run_id=scan_run_id,
                findings=findings,
                project_name=project_name,
                target_url=target_url,
                total_pages=total_pages
            )
            logger.info(f"PDF generated: {len(pdf_bytes)} bytes")
            return self._upload_to_minio(pdf_bytes, scan_run_id)
        except Exception as e:
            logger.error(f"PDF generation failed for scan {scan_run_id}: {e}", exc_info=True)
            return None
