import time
import logging
from enum import Enum
from typing import Callable, Any, Dict

logger = logging.getLogger("flawnetic.reliability")

class FailureClassification(str, Enum):
    TRANSIENT = "TRANSIENT"         # Eligible for retry
    PERMANENT = "PERMANENT"         # Immediate fail-fast
    RECOVERABLE = "RECOVERABLE"     # Fallback path available
    NON_RECOVERABLE = "NON_RECOVERABLE"

COMPONENT_RETRY_BUDGETS: Dict[str, int] = {
    "Claude": 3,
    "MinIO": 2,
    "PostgreSQL": 3,
    "Redis": 5
}

class ComponentRetryBudgetExceeded(Exception):
    pass

def execute_with_retry_budget(
    component_name: str,
    operation: Callable[[], Any],
    fallback: Callable[[], Any] = None
) -> Any:
    """
    Execute operation enforcing component retry budget and classification.
    """
    max_retries = COMPONENT_RETRY_BUDGETS.get(component_name, 3)
    attempt = 0

    while attempt < max_retries:
        try:
            return operation()
        except Exception as exc:
            attempt += 1
            logger.warning(
                f"[{component_name}] Attempt {attempt}/{max_retries} failed: {str(exc)}",
                extra={"retry_count": attempt, "error_code": "COMPONENT_RETRY"}
            )
            if attempt >= max_retries:
                if fallback:
                    logger.info(f"[{component_name}] Executing fallback path after retry exhaustion")
                    return fallback()
                raise ComponentRetryBudgetExceeded(
                    f"Component '{component_name}' retry budget ({max_retries}) exhausted. Last error: {str(exc)}"
                ) from exc
            time.sleep(0.05 * (2 ** attempt))
