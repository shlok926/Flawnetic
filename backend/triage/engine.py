import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class AITriageEngine:
    """
    Phase 1 Triage Engine for Flawnetic.
    Deduplicates findings across crawled pages and normalizes severity ratings.
    """

    def __init__(self):
        pass

    def triage(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deduplicates findings based on title + page_url combination,
        and assigns standard severity rules.
        """
        seen_keys = set()
        cleaned_findings = []

        for idx, finding in enumerate(findings, 1):
            title = finding.get("title", "Untitled Flaw")
            page_url = finding.get("page_url", "")
            module = finding.get("module", "functional")

            # Deduplication key
            dedup_key = f"{module}:{title}:{page_url}"
            if dedup_key in seen_keys:
                continue

            seen_keys.add(dedup_key)

            # Severity normalization rule
            severity = finding.get("severity", "medium").lower()
            if "sql injection" in title.lower() or "insecure login" in title.lower():
                severity = "critical"
            elif "xss" in title.lower() or "csp" in title.lower() or "internal server error" in title.lower():
                severity = "high"
            elif "wcag" in title.lower() or "hsts" in title.lower() or "overflow" in title.lower():
                severity = "medium"
            elif "console" in title.lower() or "alt" in title.lower() or "title" in title.lower():
                severity = "low"

            cleaned_finding = dict(finding)
            cleaned_finding["bug_id"] = f"FL-{idx:03d}"
            cleaned_finding["severity"] = severity
            cleaned_finding["priority"] = finding.get("priority", severity if severity in ["high", "medium", "low"] else "medium")
            
            cleaned_findings.append(cleaned_finding)

        logger.info(f"Triage completed: Reduced {len(findings)} raw findings down to {len(cleaned_findings)} unique triaged findings.")
        return cleaned_findings
