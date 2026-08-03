from typing import Optional, Dict, Any

class FlawneticException(Exception):
    """
    Centralized Enterprise Exception Model.
    Includes severity, category, root_module, recovery_recommendation, business_impact.
    """
    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        severity: str = "HIGH",
        category: str = "SYSTEM",
        root_module: Optional[str] = None,
        recovery_recommendation: Optional[str] = None,
        business_impact: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.severity = severity
        self.category = category
        self.root_module = root_module or "backend"
        self.recovery_recommendation = recovery_recommendation or "Check logs and retry operation."
        self.business_impact = business_impact or "Scan execution interrupted."
        self.correlation_id = correlation_id

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "severity": self.severity,
            "category": self.category,
            "root_module": self.root_module,
            "recovery_recommendation": self.recovery_recommendation,
            "business_impact": self.business_impact,
            "correlation_id": self.correlation_id
        }
