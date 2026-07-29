from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, JSON, Float, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
import enum
import datetime
from sqlalchemy import text

Base = declarative_base()

class RoleEnum(enum.Enum):
    admin = "admin"
    member = "member"

class ScanStatusEnum(enum.Enum):
    queued = "queued"
    crawling = "crawling"
    testing = "testing"
    generating_report = "generating_report"
    done = "done"
    failed = "failed"
    report_failed = "report_failed"

class ModuleEnum(enum.Enum):
    functional = "functional"
    security = "security"
    accessibility = "accessibility"
    visual = "visual"
    usability = "usability"

class SeverityEnum(enum.Enum):
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"

class PriorityEnum(enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"

class EvidenceTypeEnum(enum.Enum):
    screenshot = "screenshot"
    dom_snapshot = "dom_snapshot"
    console_log = "console_log"
    network_har = "network_har"
    video_trace = "video_trace"

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

class Project(Base):
    __tablename__ = "projects"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    base_url = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

class ScanRun(Base):
    __tablename__ = "scan_runs"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    status = Column(Enum(ScanStatusEnum), nullable=False)
    started_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    config = Column(JSONB)
    summary = Column(JSONB)
    site_graph = Column(JSONB)

class Page(Base):
    __tablename__ = "pages"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    scan_run_id = Column(UUID(as_uuid=True), ForeignKey("scan_runs.id"), nullable=False, index=True)
    url = Column(Text, nullable=False, index=True)
    title = Column(Text)
    http_status = Column(Integer)
    screenshot_url = Column(Text)
    discovered_via = Column(Text)

class Finding(Base):
    __tablename__ = "findings"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    scan_run_id = Column(UUID(as_uuid=True), ForeignKey("scan_runs.id"), nullable=False, index=True)
    page_id = Column(UUID(as_uuid=True), ForeignKey("pages.id"), nullable=True)
    module = Column(Enum(ModuleEnum), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    steps_to_reproduce = Column(JSONB)
    expected_result = Column(Text)
    actual_result = Column(Text)
    severity = Column(Enum(SeverityEnum), nullable=False, index=True)
    priority = Column(Enum(PriorityEnum), nullable=False)
    root_cause_hint = Column(Text, nullable=True)
    occurrence_count = Column(Integer, default=1)
    detected_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    finding_id = Column(UUID(as_uuid=True), ForeignKey("findings.id"), nullable=False)
    type = Column(Enum(EvidenceTypeEnum), nullable=False)
    storage_url = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

class Report(Base):
    __tablename__ = "reports"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    scan_run_id = Column(UUID(as_uuid=True), ForeignKey("scan_runs.id"), nullable=False)
    pdf_url = Column(Text, nullable=False)
    generated_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
