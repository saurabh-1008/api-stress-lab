from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from api_stress_lab.runner import RequestResult, RunResult


@dataclass(frozen=True)
class Metrics:
    total_requests: int
    successful_requests: int
    failed_requests: int
    timeout_count: int
    request_error_count: int
    status_code_distribution: dict[str, int]
    error_distribution: dict[str, int]
    total_bytes_received: int
    duration_seconds: float
    requests_per_second: float
    error_rate_percent: float
    min_latency_ms: float
    max_latency_ms: float
    avg_latency_ms: float
    p50_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float


def calculate_metrics(run_result: RunResult, expected_status: set[int]) -> Metrics:
    results = run_result.results
    total = len(results)
    latencies = sorted(result.latency_ms for result in results)
    successful = sum(1 for result in results if result.status_code in expected_status)
    failed = total - successful
    duration = max(run_result.duration_seconds, 0.000001)
    errors = Counter(result.error_type for result in results if result.error_type)
    statuses = Counter(str(result.status_code) for result in results if result.status_code is not None)
    total_bytes = sum(result.bytes_received for result in results)

    return Metrics(
        total_requests=total,
        successful_requests=successful,
        failed_requests=failed,
        timeout_count=errors.get("timeout", 0),
        request_error_count=errors.get("request_error", 0),
        status_code_distribution=dict(sorted(statuses.items())),
        error_distribution=dict(sorted(errors.items())),
        total_bytes_received=total_bytes,
        duration_seconds=run_result.duration_seconds,
        requests_per_second=total / duration,
        error_rate_percent=(failed / total * 100) if total else 0.0,
        min_latency_ms=latencies[0] if latencies else 0.0,
        max_latency_ms=latencies[-1] if latencies else 0.0,
        avg_latency_ms=(sum(latencies) / total) if total else 0.0,
        p50_ms=percentile(latencies, 50),
        p90_ms=percentile(latencies, 90),
        p95_ms=percentile(latencies, 95),
        p99_ms=percentile(latencies, 99),
    )


def percentile(sorted_values: list[float], percentile_value: int) -> float:
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (percentile_value / 100) * (len(sorted_values) - 1)
    lower_index = int(rank)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    fraction = rank - lower_index
    lower = sorted_values[lower_index]
    upper = sorted_values[upper_index]
    return lower + ((upper - lower) * fraction)
