from celery import Celery
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

from config.settings import settings
from models.db import ScanRun, ScanStatusEnum, Project, Page, Finding, ModuleEnum, SeverityEnum, PriorityEnum, Report
from engines.crawler.crawler import FlawneticCrawler
from engines.functional.engine import FunctionalEngine
from engines.security.engine import SecurityEngine
from engines.accessibility.engine import AccessibilityEngine
from engines.usability.engine import UsabilityEngine
from engines.visual.engine import VisualEngine
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
        
        modules_to_run = config.get("modules", ["functional", "security", "accessibility", "usability"])
        ai_analyzer = AIAnalyzer()
        pages_to_test = db.query(Page).filter(Page.scan_run_id == scan_run.id).all()
        
        if "functional" in modules_to_run:
            functional_engine = FunctionalEngine(headless=True)
            for p in pages_to_test:
                results = asyncio.run(functional_engine.analyze_and_test(p.url))
                for res in results:
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

        if "security" in modules_to_run:
            security_engine = SecurityEngine(zap_base_url=settings.zap_base_url, zap_api_key=settings.zap_api_key)
            for p in pages_to_test:
                sec_results = asyncio.run(security_engine.run_zap_dast_scan(p.url))
                for res in sec_results:
                    ai_hint = asyncio.run(ai_analyzer.analyze_finding(
                        title=res["title"],
                        description=res["description"],
                        steps=res.get("steps_to_reproduce", {})
                    ))
                    new_finding = Finding(
                        id=uuid.uuid4(),
                        scan_run_id=scan_run.id,
                        page_id=p.id,
                        module=ModuleEnum.security,
                        title=res["title"],
                        description=res["description"],
                        steps_to_reproduce=res.get("steps_to_reproduce"),
                        severity=getattr(SeverityEnum, res["severity"]),
                        priority=getattr(PriorityEnum, res["priority"]),
                        root_cause_hint=ai_hint
                    )
                    db.add(new_finding)
            db.commit()

        if "accessibility" in modules_to_run:
            a11y_engine = AccessibilityEngine(headless=True)
            for p in pages_to_test:
                a11y_results = asyncio.run(a11y_engine.scan_page(p.url))
                for res in a11y_results:
                    ai_hint = asyncio.run(ai_analyzer.analyze_finding(
                        title=res["title"],
                        description=res["description"],
                        steps=res.get("steps_to_reproduce", {})
                    ))
                    new_finding = Finding(
                        id=uuid.uuid4(),
                        scan_run_id=scan_run.id,
                        page_id=p.id,
                        module=ModuleEnum.accessibility,
                        title=res["title"],
                        description=res["description"],
                        steps_to_reproduce=res.get("steps_to_reproduce"),
                        severity=getattr(SeverityEnum, res["severity"]),
                        priority=getattr(PriorityEnum, res["priority"]),
                        root_cause_hint=ai_hint
                    )
                    db.add(new_finding)
            db.commit()

        if "usability" in modules_to_run:
            usability_engine = UsabilityEngine(headless=True)
            for p in pages_to_test:
                usability_results = asyncio.run(usability_engine.analyze_page(p.url))
                for res in usability_results:
                    ai_hint = asyncio.run(ai_analyzer.analyze_finding(
                        title=res["title"],
                        description=res["description"],
                        steps=res.get("steps_to_reproduce", {})
                    ))
                    new_finding = Finding(
                        id=uuid.uuid4(),
                        scan_run_id=scan_run.id,
                        page_id=p.id,
                        module=ModuleEnum.usability,
                        title=res["title"],
                        description=res["description"],
                        steps_to_reproduce=res.get("steps_to_reproduce"),
                        severity=getattr(SeverityEnum, res["severity"]),
                        priority=getattr(PriorityEnum, res["priority"]),
                        root_cause_hint=ai_hint
                    )
                    db.add(new_finding)
            db.commit()

        if "visual" in modules_to_run:
            visual_engine = VisualEngine(headless=True)
            for p in pages_to_test:
                visual_results = asyncio.run(visual_engine.audit_visual_rendering(p.url))
                for res in visual_results:
                    ai_hint = asyncio.run(ai_analyzer.analyze_finding(
                        title=res["title"],
                        description=res["description"],
                        steps=res.get("steps_to_reproduce", {})
                    ))
                    new_finding = Finding(
                        id=uuid.uuid4(),
                        scan_run_id=scan_run.id,
                        page_id=p.id,
                        module=ModuleEnum.visual,
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
