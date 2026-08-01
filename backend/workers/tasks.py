import os
import uuid
import asyncio
import logging
import dataclasses
from typing import List, Dict, Any

from celery import Celery
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

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

logger = logging.getLogger(__name__)

celery_app = Celery(
    "flawnetic",
    broker=settings.redis_url,
    backend=settings.redis_url
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    broker_connection_retry_on_startup=True,
)

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _run_module_safely(module_name: str, run_fn, *args, **kwargs) -> List[Dict[str, Any]]:
    """
    Run a test engine module safely.
    If the module fails, log the error and return empty list.
    The scan continues with other modules.
    """
    logger.info(f"[TASK] Starting module: {module_name}")
    try:
        result = run_fn(*args, **kwargs)
        logger.info(f"[TASK] Module {module_name} completed: {len(result)} findings")
        return result
    except Exception as e:
        logger.error(
            f"[TASK] Module {module_name} failed — scan continues without it: "
            f"{type(e).__name__}: {e}",
            exc_info=True
        )
        return []


def _get_ai_hint(ai_analyzer, title: str, description: str, steps: Any) -> Any:
    """Get AI hint if Claude API is available. Returns None otherwise."""
    if ai_analyzer is None:
        return None
    api_key = getattr(settings, 'anthropic_api_key', None)
    if not api_key or api_key in ["", "your-anthropic-api-key", "your-key-here"]:
        return None
    try:
        return asyncio.run(ai_analyzer.analyze_finding(
            title=title,
            description=description,
            steps=steps or {}
        ))
    except Exception as e:
        logger.warning(f"[AI] Analysis failed (non-fatal): {type(e).__name__}: {e}")
        return None


@celery_app.task(name="run_scan")
def run_scan(scan_run_id: str):
    db = SessionLocal()
    try:
        scan_run = db.query(ScanRun).filter(ScanRun.id == scan_run_id).first()
        if not scan_run:
            logger.error(f"[TASK] ScanRun {scan_run_id} not found in DB")
            return
            
        scan_run.status = ScanStatusEnum.crawling
        db.commit()
        
        project = db.query(Project).filter(Project.id == scan_run.project_id).first()
        if not project:
            logger.error(f"[TASK] Project for ScanRun {scan_run_id} not found")
            return
            
        config = scan_run.config or {}
        max_pages = config.get("max_pages", 50)
        max_depth = config.get("max_depth", 4)
        modules_to_run = config.get("modules", ["functional", "security", "accessibility", "usability"])
        
        logger.info(f"[TASK] Crawling: {project.base_url}")
        crawler = FlawneticCrawler(
            base_url=project.base_url,
            max_pages=max_pages,
            max_depth=max_depth,
            headless=True
        )
        
        site_graph = asyncio.run(crawler.crawl())
        logger.info(f"[TASK] Crawl finished. Total pages: {site_graph.total_pages}")
        
        # Save crawl results to DB
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
        db.commit()

        # Phase 2: Testing
        scan_run.status = ScanStatusEnum.testing
        db.commit()
        
        try:
            ai_analyzer = AIAnalyzer()
        except Exception:
            ai_analyzer = None

        pages_to_test = db.query(Page).filter(Page.scan_run_id == scan_run.id).all()
        
        # Execute Engine Modules with per-module error isolation
        if "functional" in modules_to_run:
            functional_engine = FunctionalEngine(headless=True)
            for p in pages_to_test:
                results = _run_module_safely("functional", lambda url=p.url: asyncio.run(functional_engine.analyze_and_test(url)))
                for res in results:
                    ai_hint = _get_ai_hint(ai_analyzer, res["title"], res["description"], res.get("steps_to_reproduce"))
                    new_finding = Finding(
                        id=uuid.uuid4(),
                        scan_run_id=scan_run.id,
                        page_id=p.id,
                        module=ModuleEnum.functional,
                        title=res["title"],
                        description=res["description"],
                        steps_to_reproduce=res.get("steps_to_reproduce"),
                        severity=getattr(SeverityEnum, res["severity"].lower(), SeverityEnum.medium),
                        priority=getattr(PriorityEnum, res["priority"].lower(), PriorityEnum.medium),
                        root_cause_hint=ai_hint
                    )
                    db.add(new_finding)
            db.commit()

        if "security" in modules_to_run:
            security_engine = SecurityEngine(zap_base_url=settings.zap_host, zap_api_key=settings.zap_api_key)
            for p in pages_to_test:
                sec_results = _run_module_safely("security", lambda url=p.url: asyncio.run(security_engine.run_zap_dast_scan(url)))
                for res in sec_results:
                    ai_hint = _get_ai_hint(ai_analyzer, res["title"], res["description"], res.get("steps_to_reproduce"))
                    new_finding = Finding(
                        id=uuid.uuid4(),
                        scan_run_id=scan_run.id,
                        page_id=p.id,
                        module=ModuleEnum.security,
                        title=res["title"],
                        description=res["description"],
                        steps_to_reproduce=res.get("steps_to_reproduce"),
                        severity=getattr(SeverityEnum, res["severity"].lower(), SeverityEnum.medium),
                        priority=getattr(PriorityEnum, res["priority"].lower(), PriorityEnum.medium),
                        root_cause_hint=ai_hint
                    )
                    db.add(new_finding)
            db.commit()

        if "accessibility" in modules_to_run:
            a11y_engine = AccessibilityEngine(headless=True)
            for p in pages_to_test:
                a11y_results = _run_module_safely("accessibility", lambda url=p.url: asyncio.run(a11y_engine.scan_page(url)))
                for res in a11y_results:
                    ai_hint = _get_ai_hint(ai_analyzer, res["title"], res["description"], res.get("steps_to_reproduce"))
                    new_finding = Finding(
                        id=uuid.uuid4(),
                        scan_run_id=scan_run.id,
                        page_id=p.id,
                        module=ModuleEnum.accessibility,
                        title=res["title"],
                        description=res["description"],
                        steps_to_reproduce=res.get("steps_to_reproduce"),
                        severity=getattr(SeverityEnum, res["severity"].lower(), SeverityEnum.medium),
                        priority=getattr(PriorityEnum, res["priority"].lower(), PriorityEnum.medium),
                        root_cause_hint=ai_hint
                    )
                    db.add(new_finding)
            db.commit()

        if "usability" in modules_to_run:
            usability_engine = UsabilityEngine(headless=True)
            for p in pages_to_test:
                usability_results = _run_module_safely("usability", lambda url=p.url: asyncio.run(usability_engine.analyze_page(url)))
                for res in usability_results:
                    ai_hint = _get_ai_hint(ai_analyzer, res["title"], res["description"], res.get("steps_to_reproduce"))
                    new_finding = Finding(
                        id=uuid.uuid4(),
                        scan_run_id=scan_run.id,
                        page_id=p.id,
                        module=ModuleEnum.usability,
                        title=res["title"],
                        description=res["description"],
                        steps_to_reproduce=res.get("steps_to_reproduce"),
                        severity=getattr(SeverityEnum, res["severity"].lower(), SeverityEnum.medium),
                        priority=getattr(PriorityEnum, res["priority"].lower(), PriorityEnum.medium),
                        root_cause_hint=ai_hint
                    )
                    db.add(new_finding)
            db.commit()

        if "visual" in modules_to_run:
            visual_engine = VisualEngine(headless=True)
            for p in pages_to_test:
                visual_results = _run_module_safely("visual", lambda url=p.url: asyncio.run(visual_engine.audit_visual_rendering(url)))
                for res in visual_results:
                    ai_hint = _get_ai_hint(ai_analyzer, res["title"], res["description"], res.get("steps_to_reproduce"))
                    new_finding = Finding(
                        id=uuid.uuid4(),
                        scan_run_id=scan_run.id,
                        page_id=p.id,
                        module=ModuleEnum.visual,
                        title=res["title"],
                        description=res["description"],
                        steps_to_reproduce=res.get("steps_to_reproduce"),
                        severity=getattr(SeverityEnum, res["severity"].lower(), SeverityEnum.medium),
                        priority=getattr(PriorityEnum, res["priority"].lower(), PriorityEnum.medium),
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
        
        if pdf_url:
            new_report = Report(
                id=uuid.uuid4(),
                scan_run_id=scan_run.id,
                pdf_url=pdf_url
            )
            db.add(new_report)

        # Update ScanRun status & summary
        scan_run.status = ScanStatusEnum.done
        scan_run.summary = {
            "total_pages": pages_count or 1,
            "total_findings": len(triaged_findings),
            "severity_counts": {
                "critical": sum(1 for f in triaged_findings if str(f.get("severity", "")).upper() == "CRITICAL"),
                "high": sum(1 for f in triaged_findings if str(f.get("severity", "")).upper() == "HIGH"),
                "medium": sum(1 for f in triaged_findings if str(f.get("severity", "")).upper() == "MEDIUM"),
                "low": sum(1 for f in triaged_findings if str(f.get("severity", "")).upper() == "LOW"),
            },
            "modules_run": modules_to_run,
            "pdf_url": pdf_url,
        }
        db.commit()
        logger.info(f"[TASK] ScanRun {scan_run_id} completed successfully. PDF: {pdf_url}")

    except Exception as e:
        logger.error(f"[TASK] ScanRun {scan_run_id} failed: {type(e).__name__}: {e}", exc_info=True)
        try:
            scan_run.status = ScanStatusEnum.failed
            scan_run.summary = {"error": str(e), "error_type": type(e).__name__}
            db.commit()
        except Exception as db_err:
            logger.error(f"[TASK] Failed to update scan failure status in DB: {db_err}")
    finally:
        db.close()
