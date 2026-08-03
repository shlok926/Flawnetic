import pytest
import time
import concurrent.futures
from unittest.mock import MagicMock, patch

from workers.tasks import run_scan

def test_load_testing_concurrent_scans_simulation():
    # Simulate 10 concurrent scans (Expected Production Workload)
    def run_simulated_scan(scan_id):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with patch("workers.tasks.SessionLocal", return_value=mock_db):
            run_scan(f"scan-sim-{scan_id}")
            return True

    start_time = time.perf_counter()
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(run_simulated_scan, i) for i in range(10)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result())

    total_duration = time.perf_counter() - start_time
    assert len(results) == 10
    assert all(results)
    assert total_duration < 10.0, f"10 concurrent scans simulation took too long: {total_duration:.2f}s"
