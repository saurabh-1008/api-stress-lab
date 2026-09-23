# AGENTS.md

## Project Goal
API Stress Lab is a Python async CLI tool that helps engineers test API reliability, scalability, latency, throughput, and failure behavior using config-driven load tests and human-readable reports.

## Working Rules
- Preserve user changes. Check `git status --short` before editing and do not revert unrelated work.
- Prefer small, focused changes that keep the tool usable from the CLI.
- Do not hardcode test targets, credentials, or load values in product code.
- Keep generated reports, caches, local databases, and virtual environments out of git.
- Use ASCII text unless an existing file clearly uses Unicode.

## Architecture Guidelines
- Put product code under `api_stress_lab/`.
- Keep CLI parsing, config validation, request execution, metrics, assertions, and reporting as separate modules.
- Use `httpx.AsyncClient` for HTTP execution.
- Use a bounded worker-pool model for large request counts instead of creating one asyncio task per request.
- Treat timeouts, connection errors, non-2xx responses, and assertion failures as separate concepts in metrics.

## Expected Commands
- Install dev dependencies with `pip install -e ".[dev]"`.
- Run tests with `pytest`.
- Run a sample test with `api-stress-lab run examples/simple-get.yaml`.

## Testing Expectations
- Add unit tests for config validation, percentile calculations, error-rate calculations, and assertion pass/fail behavior.
- Add at least one integration-style test using a small local FastAPI app or mocked transport.
- Verify the CLI exits with code `0` when assertions pass and non-zero when assertions fail.

## Style
- Prefer clear names over clever abstractions.
- Keep reports understandable for engineers who are not performance-testing experts.
- Document user-facing config fields in the README whenever adding or changing them.
