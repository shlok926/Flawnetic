from observability.errors import FlawneticException

def test_flawnetic_exception_structure():
    exc = FlawneticException(
        message="Database query execution timeout",
        error_code="DB_TIMEOUT",
        severity="HIGH",
        category="DATABASE",
        root_module="backend/models/db.py",
        recovery_recommendation="Verify Postgres index performance and pool sizing.",
        business_impact="Scan progress updates delayed."
    )
    d = exc.to_dict()
    assert d["error_code"] == "DB_TIMEOUT"
    assert d["severity"] == "HIGH"
    assert d["category"] == "DATABASE"
    assert "recovery_recommendation" in d
    assert "business_impact" in d
