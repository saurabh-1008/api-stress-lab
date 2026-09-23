import asyncio

import httpx

from api_stress_lab.config import LabConfig
from api_stress_lab.metrics import calculate_metrics
from api_stress_lab.runner import run_load_test


def test_runner_uses_mock_transport_without_creating_one_task_per_request() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["hello"] == "world"
        return httpx.Response(200, json={"ok": True})

    config = LabConfig.model_validate(
        {
            "target": {
                "url": "https://example.test/health",
                "method": "GET",
                "query": {"hello": "world"},
            },
            "load": {"total_requests": 5, "concurrency": 2},
            "assertions": {"expected_status": [200]},
        }
    )

    run_result = asyncio.run(run_load_test(config, transport=httpx.MockTransport(handler)))
    metrics = calculate_metrics(run_result, {200})

    assert len(run_result.results) == 5
    assert metrics.successful_requests == 5
