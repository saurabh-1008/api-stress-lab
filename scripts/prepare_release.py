"""Choose an unused stable version and stamp the CI checkout before building."""

from __future__ import annotations

import argparse
import ast
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from packaging.version import InvalidVersion, Version


PROJECT = "api-stress-lab"
ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "api_stress_lab" / "__init__.py"


def source_version(path: Path) -> str:
    module = ast.parse(path.read_text(encoding="utf-8"))
    for statement in module.body:
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__version__"
            for target in statement.targets
        ):
            value = ast.literal_eval(statement.value)
            if isinstance(value, str):
                return value
    raise ValueError("No literal __version__ assignment found")


def published_versions() -> list[str]:
    request = Request(
        f"https://pypi.org/pypi/{PROJECT}/json",
        headers={"User-Agent": "api-stress-lab-release", "Cache-Control": "no-cache"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except HTTPError as error:
        if error.code == 404:
            return []
        raise
    # Other HTTP, network, and malformed-response errors must stop publication.
    return list(payload["releases"])


def next_version(base: str, published: list[str]) -> str:
    baseline = Version(base)
    if (
        len(baseline.release) != 3
        or baseline.is_prerelease or baseline.is_devrelease
        or baseline.post is not None or baseline.local is not None or baseline.epoch
    ):
        raise ValueError("Source version must be a stable major.minor.patch version")
    versions = []
    for value in published:
        try:
            versions.append(Version(value))
        except InvalidVersion:
            continue
    stable = [value for value in versions if not value.is_prerelease and not value.is_devrelease]
    if not stable or baseline > max(stable):
        return str(baseline)
    latest = max(stable)
    major, minor, patch = (latest.release + (0, 0, 0))[:3]
    return f"{major}.{minor}.{patch + 1}"


def stamp_version(path: Path, version: str) -> None:
    source = path.read_text(encoding="utf-8")
    module = ast.parse(source)
    assignments = [
        statement for statement in module.body
        if isinstance(statement, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__version__"
            for target in statement.targets
        )
    ]
    if len(assignments) != 1:
        raise ValueError("Expected one __version__ assignment")
    assignment = assignments[0]
    if assignment.lineno != assignment.end_lineno:
        raise ValueError("Expected a single-line version assignment")
    lines = source.splitlines(keepends=True)
    lines[assignment.lineno - 1] = f'__version__ = "{version}"\n'
    path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print the next version without modifying files")
    args = parser.parse_args()
    version = next_version(source_version(VERSION_FILE), published_versions())
    if not args.dry_run:
        stamp_version(VERSION_FILE, version)
        if output := os.environ.get("GITHUB_OUTPUT"):
            with Path(output).open("a", encoding="utf-8") as file:
                file.write(f"version={version}\n")
    print(version)


if __name__ == "__main__":
    main()
