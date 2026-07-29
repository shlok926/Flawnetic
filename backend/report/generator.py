import os
import uuid
import boto3
from fpdf import FPDF
from datetime import datetime
from config.settings import settings
from typing import List

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

    def _ensure_bucket_exists(self):
        try:
            self.s3_client.head_bucket(Bucket=self.bucket)
        except:
            self.s3_client.create_bucket(Bucket=self.bucket)

    def generate_and_upload(self, scan_run_id: str, findings: List[dict], project_name: str, target_url: str) -> str:
        pdf = FPDF()
        pdf.add_page()
        
        # Title
        pdf.set_font("Arial", 'B', 18)
        pdf.cell(0, 10, "Flawnetic Automated QA & Security Report", ln=True, align='C')
        pdf.ln(5)
        
        # Metadata
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 8, f"Project: {project_name}", ln=True)
        pdf.cell(0, 8, f"Target URL: {target_url}", ln=True)
        pdf.cell(0, 8, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        pdf.cell(0, 8, f"Total Findings: {len(findings)}", ln=True)
        pdf.ln(10)
        
        # Findings List
        for idx, f in enumerate(findings, 1):
            pdf.set_font("Arial", 'B', 12)
            # Encode to avoid utf-8 char issues in standard FPDF fonts
            title = f"[{f['severity'].upper()}] {idx}. {f['title']}".encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(0, 10, title, ln=True)
            
            pdf.set_font("Arial", '', 10)
            desc = f"Description: {f['description']}".encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 6, desc)
            
            if f.get('root_cause_hint'):
                pdf.ln(2)
                pdf.set_font("Arial", 'I', 10)
                hint = f"AI Analysis & Remediation: {f['root_cause_hint']}".encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 6, hint)
                
            pdf.ln(8)
            
        # Save locally first
        file_name = f"report_{scan_run_id}.pdf"
        local_path = file_name
        pdf.output(local_path)
        
        # Upload to MinIO/S3
        s3_key = f"reports/{scan_run_id}/{file_name}"
        self.s3_client.upload_file(local_path, self.bucket, s3_key)
        
        # Clean up local file
        if os.path.exists(local_path):
            os.remove(local_path)
            
        # Return full accessible URL
        return f"{settings.s3_endpoint_url}/{self.bucket}/{s3_key}"
