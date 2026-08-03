import pytest
import gc
import tracemalloc

from report.utils import sanitize_text, compute_risk_score, sanitize_steps

def test_memory_leak_smoke_check():
    tracemalloc.start()
    gc.collect()
    snapshot1 = tracemalloc.take_snapshot()

    # Execute 10,000 text sanitizations & risk score calculations
    raw_findings = [
        {"severity": "CRITICAL", "description": "Critical vulnerability " * 10},
        {"severity": "HIGH", "description": "High vulnerability " * 10},
        {"severity": "MEDIUM", "description": "Medium vulnerability " * 10},
        {"severity": "LOW", "description": "Low vulnerability " * 10}
    ]

    for _ in range(10000):
        sanitize_text("Sanitizing text string with emojis 🔴 🟢 🟡 — dash", max_length=50)
        compute_risk_score(raw_findings)
        sanitize_steps({"step1": "Step 1 text", "step2": "Step 2 text"})

    gc.collect()
    snapshot2 = tracemalloc.take_snapshot()
    stats = snapshot2.compare_to(snapshot1, 'lineno')

    total_diff_bytes = sum(s.size_diff for s in stats)
    mem_delta_mb = total_diff_bytes / (1024 * 1024)

    tracemalloc.stop()

    # Memory growth delta after 10,000 iterations must be < 5.0 MB
    assert mem_delta_mb < 5.0, f"Memory leak detected: Heap grew by {mem_delta_mb:.2f} MB after 10k iterations"
