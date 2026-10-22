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

## Continuous Delivery

Pull requests and branches run CI checks without publishing. Once PyPI Trusted
Publishing is configured, successful pushes to `main` automatically publish a new
patch version, including documentation changes. Merge changes only when they are
ready for users. Keep release numbers in `api_stress_lab/__init__.py` as the source
baseline; setuptools derives its version from that file. Patch bumps are selected
by CI, so do not edit a duplicate version in `pyproject.toml`.

See [release setup](docs/RELEASING.md) for the one-time account configuration,
version selection, manual retries, and release troubleshooting.
