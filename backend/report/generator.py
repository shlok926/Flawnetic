"""
report/generator.py
-------------------
Enterprise PDF report generator for Flawnetic scan results.
Implements executive cover page, risk ratings (0-10), colored severity badges,
styled code boxes, finding cards, and automated QA disclaimer.
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

import boto3
from fpdf import FPDF
from config.settings import settings
from report.utils import (
    sanitize_text, sanitize_url, sanitize_steps,
    compute_risk_score, get_risk_label, format_code_snippet, truncate_text_smart,
    COLORS
)

logger = logging.getLogger(__name__)


class FlawneticPDF(FPDF):
    """FPDF subclass providing safe cell rendering methods and enterprise headers/footers."""

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", 'I', 8)
        self.set_text_color(*COLORS["text_secondary"])
        self.cell(self.epw, 10, sanitize_text(f"Confidential - Flawnetic Automated QA Platform  |  Page {self.page_no()}"), align='C')

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

    def draw_severity_badge(self, x: float, y: float, severity: str):
        """Draw a colored severity pill at position (x, y)."""
        color = COLORS.get(severity.lower(), COLORS["low"])
        self.set_fill_color(*color)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", 'B', 8)
        self.set_xy(x, y)
        self.cell(28, 6, sanitize_text(f" {severity.upper()} "), fill=True, align='C')
        self.set_text_color(*COLORS["text_primary"])

    def draw_code_box(self, code_text: str):
        """Draw a styled code/payload box with light grey background."""
        self.set_fill_color(*COLORS["code_bg"])
        self.set_draw_color(*COLORS["border"])
        self.set_font("Courier", size=8.5)
        self.set_text_color(30, 41, 59)
        self.safe_multi_cell(w=self.epw, h=5, txt=f"  {code_text}  ", border=1, fill=True)
        self.set_font("Helvetica", size=9.5)


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
        """Renders complete Enterprise PDF document into bytes buffer."""
        pdf = FlawneticPDF()
        pdf.set_auto_page_break(auto=True, margin=18)

        # -------------------------------------------------------------
        # PAGE 1: COVER PAGE
        # -------------------------------------------------------------
        pdf.add_page()
        
        # Dark Slate Header Banner Bar (#0F172A)
        pdf.set_fill_color(*COLORS["header_bg"])
        pdf.rect(0, 0, 210, 42, style='F')
        
        pdf.set_y(10)
        pdf.set_font("Helvetica", 'B', 22)
        pdf.set_text_color(*COLORS["header_text"])
        pdf.safe_cell(h=10, txt="FLAWNETIC", align='C', ln=1)
        
        pdf.set_font("Helvetica", '', 9.5)
        pdf.safe_cell(h=5, txt="AUTONOMOUS QA & SECURITY AUDIT PLATFORM", align='C', ln=1)
        pdf.ln(18)

        # Executive Title
        pdf.set_font("Helvetica", 'B', 16)
        pdf.set_text_color(*COLORS["text_primary"])
        pdf.safe_cell(h=8, txt="SECURITY & QA AUDIT REPORT", ln=1)
        pdf.set_draw_color(*COLORS["border"])
        pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
        pdf.ln(8)

        # Metadata Block
        pdf.set_font("Helvetica", '', 10)
        pdf.set_text_color(*COLORS["text_secondary"])
        pdf.safe_cell(h=6, txt=f"Project:      {project_name}", ln=1)
        pdf.safe_cell(h=6, txt=f"Target URL:   {sanitize_url(target_url, max_length=90)}", ln=1)
        pdf.safe_cell(h=6, txt=f"Scan Date:    {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}", ln=1)
        pdf.safe_cell(h=6, txt=f"Crawled:      {total_pages} Pages  |  Total Findings: {len(findings)}  |  Scan ID: {scan_run_id[:8]}", ln=1)
        pdf.ln(12)

        # Risk Score Calculation Box
        risk_score = compute_risk_score(findings)
        risk_label, risk_color = get_risk_label(risk_score)

        pdf.set_font("Helvetica", 'B', 11)
        pdf.set_text_color(*COLORS["text_primary"])
        pdf.safe_cell(h=6, txt="OVERALL RISK SCORE RATING", ln=1)
        pdf.ln(2)

        # Fill Risk Score Card Box
        curr_y = pdf.get_y()
        pdf.set_fill_color(*COLORS["code_bg"])
        pdf.set_draw_color(*COLORS["border"])
        pdf.rect(10, curr_y, 190, 24, style='FD')

        # Score Pill
        pdf.set_fill_color(*risk_color)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", 'B', 10)
        pdf.set_xy(16, curr_y + 6)
        pdf.cell(40, 12, sanitize_text(f" {risk_label} "), fill=True, align='C')

        # Score Text
        pdf.set_xy(62, curr_y + 7)
        pdf.set_font("Helvetica", 'B', 13)
        pdf.set_text_color(*COLORS["text_primary"])
        pdf.cell(0, 6, sanitize_text(f"Score: {risk_score} / 10"), ln=1)

        pdf.set_xy(62, curr_y + 13)
        pdf.set_font("Helvetica", '', 9)
        pdf.set_text_color(*COLORS["text_secondary"])
        pdf.cell(0, 5, sanitize_text("Weighted score based on Critical, High, Medium, and Low severity flaws."), ln=1)
        
        pdf.set_y(curr_y + 32)
        pdf.set_font("Helvetica", 'I', 8.5)
        pdf.set_text_color(*COLORS["text_secondary"])
        pdf.safe_cell(h=6, txt="CONFIDENTIAL - Authorized Client Use Only", align='C', ln=1)

        # -------------------------------------------------------------
        # PAGE 2: EXECUTIVE SUMMARY & MODULE STATUS
        # -------------------------------------------------------------
        pdf.add_page()
        pdf.set_font("Helvetica", 'B', 14)
        pdf.set_text_color(*COLORS["text_primary"])
        pdf.safe_cell(h=8, txt="Executive Summary & Severity Matrix", ln=1)
        pdf.ln(4)

        critical_c = sum(1 for f in findings if str(f.get("severity", "")).upper() == "CRITICAL")
        high_c = sum(1 for f in findings if str(f.get("severity", "")).upper() == "HIGH")
        medium_c = sum(1 for f in findings if str(f.get("severity", "")).upper() == "MEDIUM")
        low_c = sum(1 for f in findings if str(f.get("severity", "")).upper() == "LOW")

        # 4 Side-by-Side Severity Breakdown Cards
        y_pos = pdf.get_y()
        box_w = 44
        box_h = 22
        
        counts = [
            ("CRITICAL", critical_c, COLORS["critical"]),
            ("HIGH", high_c, COLORS["high"]),
            ("MEDIUM", medium_c, COLORS["medium"]),
            ("LOW", low_c, COLORS["low"]),
        ]

        for i, (sev_name, count_val, col_rgb) in enumerate(counts):
            x_pos = 10 + (i * 47)
            pdf.set_fill_color(*COLORS["code_bg"])
            pdf.set_draw_color(*COLORS["border"])
            pdf.rect(x_pos, y_pos, box_w, box_h, style='FD')
            
            pdf.set_fill_color(*col_rgb)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Helvetica", 'B', 7.5)
            pdf.set_xy(x_pos + 4, y_pos + 3)
            pdf.cell(36, 4, sanitize_text(f" {sev_name} "), fill=True, align='C')

            pdf.set_xy(x_pos, y_pos + 10)
            pdf.set_font("Helvetica", 'B', 12)
            pdf.set_text_color(*COLORS["text_primary"])
            pdf.cell(box_w, 8, sanitize_text(str(count_val)), align='C')

        pdf.set_y(y_pos + box_h + 10)

        # Module Audit Status Table
        pdf.set_font("Helvetica", 'B', 11)
        pdf.safe_cell(h=6, txt="Module Audit Status Summary:", ln=1)
        pdf.ln(2)

        # Table Header
        pdf.set_fill_color(*COLORS["header_bg"])
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", 'B', 9)
        pdf.cell(70, 7, sanitize_text(" Module Name"), fill=True)
        pdf.cell(60, 7, sanitize_text(" Status"), fill=True)
        pdf.cell(60, 7, sanitize_text(" Findings Count"), fill=True, new_x="LMARGIN", new_y="NEXT")

        # Table Rows
        modules_summary = [
            ("Functional Engine", "Complete", sum(1 for f in findings if str(f.get("module","")).lower() == "functional")),
            ("Security Engine (DAST)", "Complete", sum(1 for f in findings if str(f.get("module","")).lower() == "security")),
            ("Accessibility (WCAG)", "Complete", sum(1 for f in findings if str(f.get("module","")).lower() == "accessibility")),
            ("Usability & Responsiveness", "Complete", sum(1 for f in findings if str(f.get("module","")).lower() == "usability")),
            ("Visual Rendering", "Complete", sum(1 for f in findings if str(f.get("module","")).lower() == "visual")),
        ]

        pdf.set_font("Helvetica", '', 9)
        pdf.set_text_color(*COLORS["text_primary"])
        for mod_name, mod_stat, mod_cnt in modules_summary:
            pdf.set_fill_color(*COLORS["code_bg"])
            pdf.cell(70, 6, sanitize_text(f" {mod_name}"), border=1)
            pdf.cell(60, 6, sanitize_text(f" {mod_stat}"), border=1)
            pdf.cell(60, 6, sanitize_text(f" {mod_cnt} issues"), border=1, new_x="LMARGIN", new_y="NEXT")

        pdf.ln(10)

        # -------------------------------------------------------------
        # PAGES 3+: DETAILED FINDING CARDS (one per page)
        # -------------------------------------------------------------
        if not findings:
            pdf.add_page()
            pdf.set_font("Helvetica", 'B', 12)
            pdf.safe_cell(h=8, txt="Discovered Vulnerabilities & Quality Flaws", ln=1)
            pdf.ln(4)
            pdf.set_font("Helvetica", 'I', 10)
            pdf.set_text_color(*COLORS["success"])
            pdf.safe_cell(h=10, txt="No issues found - Clean Audit (0 Flaws Detected).", ln=1)
        else:
            for idx, f in enumerate(findings, 1):
                pdf.add_page()
                
                bug_id = f.get('bug_id') or f"FL-{idx:03d}"
                title = f.get('title', 'Untitled Flaw')
                sev = str(f.get('severity', 'LOW')).upper()
                mod = str(f.get('module', 'functional')).upper()

                # Card Header Bar
                curr_y = pdf.get_y()
                pdf.set_fill_color(*COLORS["header_bg"])
                pdf.rect(10, curr_y, 190, 10, style='F')

                pdf.set_xy(12, curr_y + 2)
                pdf.set_font("Helvetica", 'B', 10)
                pdf.set_text_color(255, 255, 255)
                pdf.cell(140, 6, sanitize_text(f"{bug_id}  |  {title}", max_length=65))

                pdf.draw_severity_badge(170, curr_y + 2, sev)
                pdf.set_y(curr_y + 14)

                # Metadata Metadata Grid
                pdf.set_font("Helvetica", '', 8.5)
                pdf.set_text_color(*COLORS["text_secondary"])
                pdf.safe_cell(h=5, txt=f"Target URL: {sanitize_url(f.get('page_url'), max_length=95)}", ln=1)
                pdf.safe_cell(h=5, txt=f"Module: {mod}   |   Impact Category: Input Validation & Security Integrity", ln=1)
                pdf.ln(3)

                # Description
                pdf.set_font("Helvetica", 'B', 9.5)
                pdf.set_text_color(*COLORS["text_primary"])
                pdf.safe_cell(h=5, txt="Business Impact & Description:", ln=1)
                pdf.set_font("Helvetica", '', 9)
                pdf.set_text_color(51, 65, 85)
                desc = truncate_text_smart(f.get('description', 'No detailed description provided.'), limit=600)
                pdf.safe_multi_cell(h=4.5, txt=desc)
                pdf.ln(3)

                # Steps to Reproduce & Code Box
                pdf.set_font("Helvetica", 'B', 9.5)
                pdf.set_text_color(*COLORS["text_primary"])
                pdf.safe_cell(h=5, txt="Steps to Reproduce & Code Payload:", ln=1)
                
                steps_list = sanitize_steps(f.get('steps_to_reproduce'))
                pdf.set_font("Helvetica", '', 8.5)
                pdf.set_text_color(51, 65, 85)
                for step in steps_list:
                    pdf.safe_multi_cell(h=4.5, txt=f"  {step}")
                pdf.ln(2)

                # Payload / Code Snippet Box
                payload_code = format_code_snippet(f.get('payload') or f.get('description', 'N/A')[:100], max_length=200)
                pdf.draw_code_box(payload_code)
                pdf.ln(3)

                # Expected Result
                pdf.set_font("Helvetica", 'B', 9)
                pdf.set_text_color(*COLORS["text_primary"])
                pdf.safe_cell(h=4.5, txt="Expected Result:", ln=1)
                pdf.set_font("Helvetica", '', 8.5)
                pdf.set_text_color(51, 65, 85)
                exp = truncate_text_smart(f.get('expected_result', 'System should validate input securely without errors.'), limit=500)
                pdf.safe_multi_cell(h=4.5, txt=exp)
                pdf.ln(2)

                # Actual Result
                pdf.set_font("Helvetica", 'B', 9)
                pdf.set_text_color(*COLORS["text_primary"])
                pdf.safe_cell(h=4.5, txt="Actual Result:", ln=1)
                pdf.set_font("Helvetica", '', 8.5)
                pdf.set_text_color(51, 65, 85)
                act = truncate_text_smart(f.get('actual_result', 'Anomalous behavior or unhandled exception observed during scan.'), limit=500)
                pdf.safe_multi_cell(h=4.5, txt=act)
                pdf.ln(3)

                # AI Root Cause & Remediation Hint
                hint = f.get('root_cause_hint')
                if hint:
                    pdf.set_font("Helvetica", 'B', 9.5)
                    pdf.set_text_color(22, 101, 52) # Dark green
                    pdf.safe_cell(h=5, txt="AI Root Cause Analysis & Code Remediation Patch:", ln=1)
                    pdf.set_font("Helvetica", 'I', 8.5)
                    pdf.set_text_color(22, 101, 52)
                    pdf.safe_multi_cell(h=4.5, txt=truncate_text_smart(hint, limit=600))

        # -------------------------------------------------------------
        # LAST PAGE: DISCLAIMER & AUDIT SCOPE
        # -------------------------------------------------------------
        pdf.add_page()
        pdf.set_font("Helvetica", 'B', 12)
        pdf.set_text_color(*COLORS["text_primary"])
        pdf.safe_cell(h=8, txt="Audit Scope & Automated Testing Disclaimer", ln=1)
        pdf.set_draw_color(*COLORS["border"])
        pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
        pdf.ln(6)

        disclaimer_text = (
            "This report was automatically generated by Flawnetic Autonomous QA Platform. "
            "Automated scanning provides rapid detection of common web vulnerabilities, accessibility failures, "
            "and usability regressions. However, automated testing cannot replace comprehensive manual penetration testing "
            "or manual code review. All tests were executed against authorized endpoints under configured scan bounds."
        )

        pdf.set_font("Helvetica", '', 9)
        pdf.set_text_color(*COLORS["text_secondary"])
        pdf.safe_multi_cell(h=5, txt=disclaimer_text)
        pdf.ln(10)

        pdf.set_font("Helvetica", 'B', 10)
        pdf.set_text_color(*COLORS["text_primary"])
        pdf.safe_cell(h=6, txt="Scan Execution Bounds & Environment:", ln=1)
        pdf.set_font("Helvetica", '', 8.5)
        pdf.safe_cell(h=5, txt=f"  - Flawnetic Engine Version: 1.0.0 Enterprise", ln=1)
        pdf.safe_cell(h=5, txt=f"  - Target Hostname: {target_url}", ln=1)
        pdf.safe_cell(h=5, txt=f"  - Pages Analyzed: {total_pages}", ln=1)
        pdf.safe_cell(h=5, txt=f"  - Report Generation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}", ln=1)

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
                presigned_url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket, 'Key': s3_key},
                    ExpiresIn=604800 # 7 days
                )
                
                # Replace Docker internal endpoint URL with browser-accessible public URL
                public_url = presigned_url
                if getattr(settings, 's3_public_url', None):
                    public_url = presigned_url.replace(settings.s3_endpoint_url, settings.s3_public_url)
                    public_url = public_url.replace("http://minio:9000", settings.s3_public_url)

                logger.info(f"PDF uploaded to MinIO: {public_url}")
                return public_url
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
