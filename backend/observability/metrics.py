import time
from typing import Dict, Any

class MetricsRegistry:
    """
    Categorized Enterprise Metrics Taxonomy:
    - System Metrics (CPU, RAM, Open Handles)
    - Application Metrics (API latency, Scan duration, Queue depth)
    - Business Metrics (Successful/Failed Scans, Findings by Severity)
    - AI Metrics (Claude latency, AI fallback count, Prompt validation blocks)
    """
    def __init__(self):
        self.counters = {
            "api_requests_total": 0,
            "scans_started_total": 0,
            "scans_successful_total": 0,
            "scans_failed_total": 0,
            "reports_generated_total": 0,
            "ai_invocations_total": 0,
            "ai_fallback_total": 0,
            "ai_prompt_injection_blocks": 0
        }
        self.gauges = {
            "queue_depth": 0,
            "active_worker_threads": 0,
            "active_browser_contexts": 0,
            "memory_usage_mb": 0.0,
            "cpu_usage_pct": 0.0
        }
        self.histograms = {
            "api_request_duration_ms": [],
            "scan_duration_seconds": [],
            "pdf_duration_seconds": [],
            "ai_duration_seconds": []
        }

    def inc_counter(self, name: str, value: int = 1):
        if name in self.counters:
            self.counters[name] += value

    def set_gauge(self, name: str, value: float):
        if name in self.gauges:
            self.gauges[name] = value

    def observe_histogram(self, name: str, value: float):
        if name in self.histograms:
            self.histograms[name].append(value)
            # Keep max 1000 observations
            if len(self.histograms[name]) > 1000:
                self.histograms[name].pop(0)

    def get_metrics_snapshot(self) -> Dict[str, Any]:
        return {
            "system_metrics": {
                "memory_usage_mb": self.gauges["memory_usage_mb"],
                "cpu_usage_pct": self.gauges["cpu_usage_pct"],
                "active_browser_contexts": self.gauges["active_browser_contexts"]
            },
            "application_metrics": {
                "api_requests_total": self.counters["api_requests_total"],
                "queue_depth": self.gauges["queue_depth"],
                "active_workers": self.gauges["active_worker_threads"],
                "avg_api_latency_ms": (
                    sum(self.histograms["api_request_duration_ms"]) / max(1, len(self.histograms["api_request_duration_ms"]))
                )
            },
            "business_metrics": {
                "scans_started_total": self.counters["scans_started_total"],
                "scans_successful_total": self.counters["scans_successful_total"],
                "scans_failed_total": self.counters["scans_failed_total"],
                "reports_generated_total": self.counters["reports_generated_total"]
            },
            "ai_metrics": {
                "ai_invocations_total": self.counters["ai_invocations_total"],
                "ai_fallback_total": self.counters["ai_fallback_total"],
                "ai_prompt_injection_blocks": self.counters["ai_prompt_injection_blocks"]
            }
        }

metrics_registry = MetricsRegistry()
