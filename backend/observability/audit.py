import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional

from observability.logging import correlation_id_var, user_id_var, SCHEMA_VERSION

class AuditEventType(str, Enum):
    USER_REGISTER = "USER_REGISTER"
    USER_LOGIN = "USER_LOGIN"
    PROJECT_CREATED = "PROJECT_CREATED"
    PROJECT_DELETED = "PROJECT_DELETED"
    SCAN_TRIGGERED = "SCAN_TRIGGERED"
    SCAN_CANCELLED = "SCAN_CANCELLED"
    REPORT_DOWNLOADED = "REPORT_DOWNLOADED"
    API_KEY_REVOKED = "API_KEY_REVOKED"
    ROLE_CHANGED = "ROLE_CHANGED"

audit_logger = logging.getLogger("flawnetic.audit")

def log_audit_event(
    event_type: AuditEventType,
    resource_id: str,
    action_by_user_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Log an immutable security audit event.
    Separate from operational diagnostic logs.
    """
    audit_record = {
        "schema_version": SCHEMA_VERSION,
        "event_category": "AUDIT",
        "event_type": event_type.value,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "correlation_id": correlation_id_var.get(),
        "user_id": action_by_user_id or user_id_var.get() or "ANONYMOUS",
        "resource_id": resource_id,
        "metadata": metadata or {}
    }
    audit_logger.info(json.dumps(audit_record))
    return audit_record
