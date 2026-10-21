# Contributing

Use Python 3.11+ and a virtual environment:

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

Product code lives in `api_stress_lab/`; examples and the local demo live in
`examples/`. Keep changes focused, preserve existing work, and add tests for
behavior changes. Network tests should use local servers or HTTPX mock transports.
Update README and the user guide when changing configuration or metrics.

Never commit credentials, local databases, private configs, or generated reports.
Use `*.local.yaml` for personal test configurations. Read `AGENTS.md` for repository
conventions. Release checks are `python -m build` followed by
`python -m twine check --strict dist/*`.

Open an issue describing the expected behavior, actual behavior, Python version,
and a minimal configuration with all secrets removed. Contributions are under MIT.
