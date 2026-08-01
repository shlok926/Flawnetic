import os
import base64
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import boto3
from jinja2 import Environment, FileSystemLoader
from fpdf import FPDF
from config.settings import settings

logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """Replaces Unicode special characters with ASCII equivalents and encodes safely for FPDF Latin-1."""
    if not text:
        return ""
    if not isinstance(text, str):
        text = str(text)

    replacements = [
        ('—', '-'),
        ('–', '-'),
        ('\u2014', '-'),
        ('\u2013', '-'),
        ('\u2018', "'"),
        ('\u2019', "'"),
        ('\u201c', '"'),
        ('\u201d', '"'),
        ('→', '->'),
        ('←', '<-'),
        ('✓', 'OK'),
        ('✗', 'FAIL'),
        ('🔴', '[CRITICAL]'),
        ('🟠', '[HIGH]'),
        ('🟡', '[MEDIUM]'),
        ('🔵', '[LOW]'),
    ]
    for orig, repl in replacements:
        text = text.replace(orig, repl)

    return text.encode('latin-1', 'replace').decode('latin-1')


class PDFReportGenerator:
    def __init__(self):
        # Connect to MinIO/S3
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name=settings.s3_region
        )
        self.bucket = settings.s3_bucket_name
        self._ensure_bucket_exists()

        # Jinja2 template loader
        template_dir = Path(__file__).parent / "templates"
        self.jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))

    def _ensure_bucket_exists(self):
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
        except Exception:
            try:
                self.s3_client.create_bucket(Bucket=self.bucket)
            except Exception as e:
                logger.warning(f"S3 bucket creation check warning: {e}")

    def _encode_image_to_base64(self, image_path: str) -> str:
        """Reads local screenshot image file and converts to base64 string."""
        if not image_path or not os.path.exists(image_path):
            return ""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except Exception as e:
            logger.warning(f"Error encoding screenshot image {image_path}: {e}")
            return ""

    def render_html_report(
        self, 
        scan_run_id: str, 
        findings: List[Dict[str, Any]], 
        project_name: str, 
        target_url: str,
        total_pages: int = 1
    ) -> str:
        """Loads report.html.j2 template and renders HTML string with findings and statistics."""
        template = self.jinja_env.get_template("report.html.j2")

        # Compute severity breakdown counts
        critical_count = sum(1 for f in findings if f.get("severity", "").lower() == "critical")
        high_count = sum(1 for f in findings if f.get("severity", "").lower() == "high")
        medium_count = sum(1 for f in findings if f.get("severity", "").lower() == "medium")
        low_count = sum(1 for f in findings if f.get("severity", "").lower() == "low")

        # Format findings with base64 screenshots and bug IDs
        formatted_findings = []
        for idx, f in enumerate(findings, 1):
            finding_dict = dict(f)
            finding_dict["bug_id"] = f.get("bug_id") or f"FL-{idx:03d}"
            finding_dict["severity"] = f.get("severity", "medium").upper()
            finding_dict["module"] = f.get("module", "functional").upper()
            
            # Screenshot base64 processing
            screenshot_path = f.get("screenshot_path") or f.get("evidence", {}).get("screenshot_url")
            if screenshot_path:
                finding_dict["screenshot_base64"] = self._encode_image_to_base64(screenshot_path)
            else:
                finding_dict["screenshot_base64"] = ""

            # Steps to reproduce
            steps = f.get("steps_to_reproduce")
            if isinstance(steps, dict):
                finding_dict["steps_list"] = [f"{k}: {v}" for k, v in steps.items()]
            elif isinstance(steps, list):
                finding_dict["steps_list"] = steps
            else:
                finding_dict["steps_list"] = []

            formatted_findings.append(finding_dict)

        context = {
            "project_name": project_name,
            "base_url": target_url,
            "scan_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "total_pages": total_pages,
            "total_findings": len(findings),
            "critical_count": critical_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "low_count": low_count,
            "findings": formatted_findings
        }

        return template.render(**context)

    def generate_and_upload(
        self, 
        scan_run_id: str, 
        findings: List[Dict[str, Any]], 
        project_name: str, 
        target_url: str,
        total_pages: int = 1
    ) -> str:
        """Generates PDF report using FPDF2, uploads to MinIO/S3, and returns public URL."""
        pdf_file_name = f"report_{scan_run_id}.pdf"
        local_pdf_path = pdf_file_name

        pdf = FPDF()
        pdf.add_page()
        
        # Header Logo & Title
        pdf.set_font("Arial", 'B', 18)
        pdf.set_text_color(79, 70, 229)
        pdf.cell(pdf.epw, 10, clean_text("Flawnetic AI Audit Report"), new_x="LMARGIN", new_y="NEXT", align='C')
        pdf.set_font("Arial", '', 10)
        pdf.set_text_color(100, 116, 139)
        pdf.cell(pdf.epw, 6, clean_text("Autonomous E2E QA & Security Platform"), new_x="LMARGIN", new_y="NEXT", align='C')
        pdf.ln(8)

        # Metadata Box
        pdf.set_font("Arial", 'B', 12)
        pdf.set_text_color(15, 23, 42)
        pdf.cell(pdf.epw, 8, clean_text(f"Project: {project_name}"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Arial", '', 10)
        pdf.cell(pdf.epw, 6, clean_text(f"Target URL: {target_url}"), new_x="LMARGIN", new_y="NEXT")
        pdf.cell(pdf.epw, 6, clean_text(f"Scan Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"), new_x="LMARGIN", new_y="NEXT")
        pdf.cell(pdf.epw, 6, clean_text(f"Pages Crawled: {total_pages} | Total Findings: {len(findings)}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(8)

        # Severity Summary Table
        critical_c = sum(1 for f in findings if f.get("severity", "").lower() == "critical")
        high_c = sum(1 for f in findings if f.get("severity", "").lower() == "high")
        medium_c = sum(1 for f in findings if f.get("severity", "").lower() == "medium")
        low_c = sum(1 for f in findings if f.get("severity", "").lower() == "low")

        pdf.set_font("Arial", 'B', 11)
        pdf.cell(pdf.epw, 8, clean_text("Severity Summary Breakdown:"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Arial", '', 10)
        pdf.cell(pdf.epw, 6, clean_text(f"  Critical: {critical_c} | High: {high_c} | Medium: {medium_c} | Low: {low_c}"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(10)

        # Findings Section
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(pdf.epw, 8, clean_text("Discovered Findings & Flaws:"), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        if not findings:
            pdf.set_font("Arial", 'I', 11)
            pdf.set_text_color(16, 185, 129)
            pdf.cell(pdf.epw, 10, clean_text("No issues found - Clean Audit (0 Flaws Detected)."), new_x="LMARGIN", new_y="NEXT")
        else:
            for idx, f in enumerate(findings, 1):
                pdf.set_font("Arial", 'B', 10)
                pdf.set_text_color(15, 23, 42)
                bug_id = f.get('bug_id') or f"FL-{idx:03d}"
                sev = f.get('severity', 'MEDIUM').upper()
                title = f.get('title', 'Untitled Flaw')
                mod = f.get('module', 'FUNCTIONAL').upper()

                title_line = f"{bug_id} [{sev}] [{mod}] {title}"
                pdf.cell(pdf.epw, 7, clean_text(title_line), new_x="LMARGIN", new_y="NEXT")

                pdf.set_font("Arial", '', 9)
                pdf.set_text_color(51, 65, 85)
                if f.get('page_url'):
                    pdf.cell(pdf.epw, 5, clean_text(f"URL: {f.get('page_url')}"), new_x="LMARGIN", new_y="NEXT")
                
                desc = f.get('description', '')
                if desc:
                    pdf.multi_cell(pdf.epw, 5, clean_text(f"Description: {desc}"))

                if f.get('root_cause_hint'):
                    pdf.set_font("Arial", 'I', 9)
                    pdf.set_text_color(22, 101, 52)
                    pdf.multi_cell(pdf.epw, 5, clean_text(f"AI Remediation: {f.get('root_cause_hint')}"))

                pdf.ln(6)

        # Footer
        pdf.set_y(-15)
        pdf.set_font("Arial", 'I', 8)
        pdf.set_text_color(148, 163, 184)
        pdf.cell(pdf.epw, 10, clean_text("Generated by Flawnetic - Automated QA Platform"), align='C')

        pdf.output(local_pdf_path)

        # Upload generated PDF to MinIO/S3
        s3_key = f"reports/{scan_run_id}/{pdf_file_name}"
        try:
            self.s3_client.upload_file(local_pdf_path, self.bucket, s3_key)
        except Exception as e:
            logger.error(f"S3 upload error: {e}")

        # Cleanup local PDF
        if os.path.exists(local_pdf_path):
            os.remove(local_pdf_path)

        # Return presigned/accessible URL
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': s3_key},
                ExpiresIn=604800 # 7 days
            )
            return url
        except Exception:
            return f"{settings.s3_endpoint_url}/{self.bucket}/{s3_key}"
