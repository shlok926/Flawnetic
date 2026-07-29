from celery import Celery
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

from config.settings import settings
from models.db import ScanRun, ScanStatusEnum, Project, Page, Finding, ModuleEnum, SeverityEnum, PriorityEnum, Report
from engines.crawler.crawler import FlawneticCrawler
from engines.functional.engine import FunctionalEngine
from engines.ai.analyzer import AIAnalyzer
from report.generator import PDFReportGenerator
import asyncio
import uuid

celery_app = Celery(
    "flawnetic_worker",
    broker=settings.redis_url,
    backend=settings.redis_url
)

# Avoid pooling issues in Celery workers by not using NullPool here, or explicitly manage
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@celery_app.task(name="run_scan")
def run_scan(scan_run_id: str):
    db = SessionLocal()
    try:
        scan_run = db.query(ScanRun).filter(ScanRun.id == scan_run_id).first()
        if not scan_run:
            return
            
        scan_run.status = ScanStatusEnum.crawling
        db.commit()
        
        # Get project for base_url
        project = db.query(Project).filter(Project.id == scan_run.project_id).first()
        if not project:
            return
            
        # Extract config
        config = scan_run.config or {}
        max_pages = config.get("max_pages", 50)
        max_depth = config.get("max_depth", 4)
        
        # Initialize and run Crawler (Async execution inside sync celery)
        crawler = FlawneticCrawler(
            base_url=project.base_url,
            max_pages=max_pages,
            max_depth=max_depth,
            headless=True
        )
        
        site_graph = asyncio.run(crawler.crawl())
        
        # Save results to DB
        scan_run.site_graph = site_graph.model_dump()
        
        for p in site_graph.pages:
            new_page = Page(
                id=uuid.uuid4(),
                scan_run_id=scan_run.id,
                url=p.url,
                title=p.title,
                http_status=p.status_code,
                screenshot_url=p.screenshot_path
            )
            db.add(new_page)
            
        # Phase 2: Testing
        scan_run.status = ScanStatusEnum.testing
        db.commit()
        
        modules_to_run = config.get("modules", [])
        
        if "functional" in modules_to_run:
            functional_engine = FunctionalEngine(headless=True)
            ai_analyzer = AIAnalyzer()
            pages_to_test = db.query(Page).filter(Page.scan_run_id == scan_run.id).all()
            
            for p in pages_to_test:
                results = asyncio.run(functional_engine.analyze_and_test(p.url))
                
                for res in results:
                    # AI Remediation Enrichment
                    ai_hint = asyncio.run(ai_analyzer.analyze_finding(
                        title=res["title"],
                        description=res["description"],
                        steps=res.get("steps_to_reproduce", {})
                    ))

                    new_finding = Finding(
                        id=uuid.uuid4(),
                        scan_run_id=scan_run.id,
                        page_id=p.id,
                        module=ModuleEnum.functional,
                        title=res["title"],
                        description=res["description"],
                        steps_to_reproduce=res.get("steps_to_reproduce"),
                        severity=getattr(SeverityEnum, res["severity"]),
                        priority=getattr(PriorityEnum, res["priority"]),
                        root_cause_hint=ai_hint
                    )
                    db.add(new_finding)
            db.commit()

        # Phase 3: Report Generation
        report_gen = PDFReportGenerator()
        all_findings = db.query(Finding).filter(Finding.scan_run_id == scan_run.id).all()
        findings_data = [
            {
                "title": f.title,
                "description": f.description,
                "severity": f.severity.name,
                "root_cause_hint": f.root_cause_hint
            } for f in all_findings
        ]
        
        pdf_url = report_gen.generate_and_upload(
            scan_run_id=str(scan_run.id),
            findings=findings_data,
            project_name=project.name,
            target_url=project.base_url
        )
        
        new_report = Report(
            id=uuid.uuid4(),
            scan_run_id=scan_run.id,
            pdf_url=pdf_url
        )
        db.add(new_report)

        scan_run.status = ScanStatusEnum.done
        db.commit()
    except Exception as e:
        scan_run.status = ScanStatusEnum.failed
        db.commit()
    finally:
        db.close()
