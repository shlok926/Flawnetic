from observability.audit import log_audit_event, AuditEventType

def test_audit_event_logging():
    record = log_audit_event(
        event_type=AuditEventType.REPORT_DOWNLOADED,
        resource_id="scan-report-123",
        action_by_user_id="user-sec-01",
        metadata={"format": "pdf"}
    )
    assert record["event_category"] == "AUDIT"
    assert record["event_type"] == "REPORT_DOWNLOADED"
    assert record["user_id"] == "user-sec-01"
    assert record["resource_id"] == "scan-report-123"
