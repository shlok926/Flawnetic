import pytest
from observability.reliability import execute_with_retry_budget, ComponentRetryBudgetExceeded

def test_component_retry_budget_success():
    attempts = 0
    def op():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ValueError("Transient error")
        return "success"

    res = execute_with_retry_budget("Claude", op)
    assert res == "success"
    assert attempts == 2

def test_component_retry_budget_exceeded_fallback():
    def failing_op():
        raise RuntimeError("MinIO connection failed")

    def fallback_op():
        return "local_file_saved"

    res = execute_with_retry_budget("MinIO", failing_op, fallback=fallback_op)
    assert res == "local_file_saved"
