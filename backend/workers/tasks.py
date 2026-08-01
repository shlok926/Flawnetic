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
from triage.engine import AITriageEngine
from report.generator import PDFReportGenerator
import asyncio
import uuid

celery_app = Celery(
    "flawnetic",
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
        import dataclasses
        scan_run.site_graph = dataclasses.asdict(site_graph)
        
        for p in site_graph.pages:
            new_page = Page(
                id=uuid.uuid4(),
                scan_run_id=scan_run.id,
                url=p.url,
                title=p.title,
                http_status=p.http_status,
                screenshot_url=p.screenshot_path
            )
            db.add(new_page)
            
        # Phase 2: Testing
        scan_run.status = ScanStatusEnum.testing
        db.commit()
        
        modules_to_run = config.get("modules", ["functional", "security", "accessibility", "usability"])
        try:
            ai_analyzer = AIAnalyzer()
        except Exception:
            ai_analyzer = None

        pages_to_test = db.query(Page).filter(Page.scan_run_id == scan_run.id).all()
        
        def get_ai_hint(res):
            ai_hint = None
            if ai_analyzer and getattr(settings, 'anthropic_api_key', None) and settings.anthropic_api_key != "your-anthropic-api-key":
                try:
                    ai_hint = asyncio.run(ai_analyzer.analyze_finding(
                        title=res["title"],
                        description=res["description"],
                        steps=res.get("steps_to_reproduce", {})
                    ))
                except Exception as ai_err:
                    print(f"[AI WARNING] AI analysis failed: {ai_err}")
                    ai_hint = None
            return ai_hint

        if "functional" in modules_to_run:
            functional_engine = FunctionalEngine(headless=True)
            for p in pages_to_test:
                results = asyncio.run(functional_engine.analyze_and_test(p.url))
                for res in results:
                    ai_hint = get_ai_hint(res)
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
            security_engine = SecurityEngine(zap_base_url=settings.zap_host, zap_api_key=settings.zap_api_key)
            for p in pages_to_test:
                sec_results = asyncio.run(security_engine.run_zap_dast_scan(p.url))
                for res in sec_results:
                    ai_hint = get_ai_hint(res)
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
                    ai_hint = get_ai_hint(res)
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
                    ai_hint = get_ai_hint(res)
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
                    ai_hint = get_ai_hint(res)
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

        # Phase 3: Report Generation & Triage
        report_gen = PDFReportGenerator()
        triage_engine = AITriageEngine()

        all_findings = db.query(Finding).filter(Finding.scan_run_id == scan_run.id).all()
        pages_count = db.query(Page).filter(Page.scan_run_id == scan_run.id).count()

        raw_findings_data = []
        for f in all_findings:
            page_obj = db.query(Page).filter(Page.id == f.page_id).first() if f.page_id else None
            raw_findings_data.append({
                "title": f.title,
                "description": f.description,
                "severity": f.severity.name if hasattr(f.severity, 'name') else str(f.severity),
                "module": f.module.name if hasattr(f.module, 'name') else str(f.module),
                "steps_to_reproduce": f.steps_to_reproduce,
                "root_cause_hint": f.root_cause_hint,
                "page_url": page_obj.url if page_obj else project.base_url,
                "screenshot_path": page_obj.screenshot_url if page_obj else None
            })

        # Run Triage Engine
        triaged_findings = triage_engine.triage(raw_findings_data)

        pdf_url = report_gen.generate_and_upload(
            scan_run_id=str(scan_run.id),
            findings=triaged_findings,
            project_name=project.name,
            target_url=project.base_url,
            total_pages=pages_count or 1
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
        import traceback
        print(f"[SCAN FAILED] scan_run_id={scan_run_id}")
        print(f"[ERROR] {type(e).__name__}: {e}")
        print(traceback.format_exc())
        try:
            scan_run.status = ScanStatusEnum.failed
            scan_run.summary = {"error": str(e), "error_type": type(e).__name__}
            db.commit()
        except:
            pass
    finally:
        db.close()
