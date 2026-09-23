from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any

import httpx

from api_stress_lab.config import LabConfig


@dataclass(frozen=True)
class RequestResult:
    latency_ms: float
    status_code: int | None
    ok: bool
    error_type: str | None = None
    error_message: str | None = None
    bytes_received: int = 0


@dataclass(frozen=True)
class RunResult:
    results: list[RequestResult]
    duration_seconds: float


async def run_load_test(
    config: LabConfig,
    transport: httpx.AsyncBaseTransport | None = None,
) -> RunResult:
    next_request = 0
    lock = asyncio.Lock()
    results: list[RequestResult] = []
    started_at = time.perf_counter()

    async with httpx.AsyncClient(
        timeout=config.load.timeout_seconds,
        transport=transport,
    ) as client:

        async def worker(worker_index: int) -> None:
            nonlocal next_request
            if config.load.ramp_up_seconds > 0:
                delay = (config.load.ramp_up_seconds / config.load.concurrency) * worker_index
                await asyncio.sleep(delay)

            while True:
                async with lock:
                    if next_request >= config.load.total_requests:
                        return
                    next_request += 1

                result = await send_request(client, config)
                results.append(result)

        workers = [
            asyncio.create_task(worker(index))
            for index in range(config.load.concurrency)
        ]
        await asyncio.gather(*workers)

    duration_seconds = time.perf_counter() - started_at
    return RunResult(results=results, duration_seconds=duration_seconds)


async def send_request(client: httpx.AsyncClient, config: LabConfig) -> RequestResult:
    started_at = time.perf_counter()
    try:
        response = await client.request(
            method=config.target.method,
            url=config.target.url,
            headers=config.target.headers,
            params=config.target.query,
            json=_json_body(config.target.body),
            content=_raw_body(config.target.body),
        )
        latency_ms = (time.perf_counter() - started_at) * 1000
        return RequestResult(
            latency_ms=latency_ms,
            status_code=response.status_code,
            ok=response.is_success,
            bytes_received=len(response.content),
        )
    except httpx.TimeoutException as error:
        return _error_result(started_at, "timeout", str(error))
    except httpx.RequestError as error:
        return _error_result(started_at, "request_error", str(error))


def _json_body(body: Any | None) -> Any | None:
    if isinstance(body, dict | list):
        return body
    return None


def _raw_body(body: Any | None) -> bytes | str | None:
    if body is None or isinstance(body, dict | list):
        return None
    return str(body)


def _error_result(started_at: float, error_type: str, error_message: str) -> RequestResult:
    latency_ms = (time.perf_counter() - started_at) * 1000
    return RequestResult(
        latency_ms=latency_ms,
        status_code=None,
        ok=False,
        error_type=error_type,
        error_message=error_message,
    )
