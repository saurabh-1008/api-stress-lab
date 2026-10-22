import io
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

from scripts import prepare_release


@pytest.mark.parametrize(("base", "published", "expected"), [
    ("0.1.0", [], "0.1.0"),
    ("0.1.0", ["0.1.0"], "0.1.1"),
    ("0.1.0", ["0.1.9", "0.1.10", "0.1.2"], "0.1.11"),
    ("0.2.0", ["0.1.9"], "0.2.0"),
    ("0.1.0", ["0.2.0"], "0.2.1"),
    ("0.1.0", ["garbage", "0.1.0", "1.0.0rc1", "1.0.0.dev1"], "0.1.1"),
    ("0.1.0", ["0.1.0", "0.1.1.post1"], "0.1.2"),
])
def test_next_release_is_unused_and_newer(base, published, expected):
    assert prepare_release.next_version(base, published) == expected


@pytest.mark.parametrize("base", ["0.1", "0.1.0rc1", "0.1.0.dev1", "0.1.0+local", "1!0.1.0"])
def test_source_baseline_must_be_a_stable_three_part_version(base):
    with pytest.raises(ValueError):
        prepare_release.next_version(base, [])


def test_stamping_preserves_other_source_and_updates_metadata_input(tmp_path):
    path = tmp_path / "__init__.py"
    path.write_text('"""Package description."""\n\n__version__ = "0.1.0"\nother = 42\n', encoding="utf-8")
    prepare_release.stamp_version(path, "0.1.1")
    assert prepare_release.source_version(path) == "0.1.1"
    assert '"""Package description."""' in path.read_text(encoding="utf-8")
    assert "other = 42" in path.read_text(encoding="utf-8")


def test_fetch_includes_yanked_versions_to_avoid_reusing_them(monkeypatch):
    payload = b'{"releases":{"0.1.0":[],"0.1.1":[{"yanked":true}]}}'
    monkeypatch.setattr(prepare_release, "urlopen", lambda *args, **kwargs: io.BytesIO(payload))
    assert prepare_release.published_versions() == ["0.1.0", "0.1.1"]


def test_first_upload_handles_missing_pypi_project(monkeypatch):
    def missing(*args, **kwargs):
        raise HTTPError("https://pypi.org/", 404, "Not found", {}, None)
    monkeypatch.setattr(prepare_release, "urlopen", missing)
    assert prepare_release.published_versions() == []


def test_network_failure_stops_release_without_changing_source(tmp_path, monkeypatch):
    path = tmp_path / "__init__.py"
    original = '__version__ = "0.1.0"\n'
    path.write_text(original, encoding="utf-8")
    monkeypatch.setattr(prepare_release, "VERSION_FILE", path)
    monkeypatch.setattr("sys.argv", ["prepare_release.py"])
    def unavailable(*args, **kwargs):
        raise URLError("PyPI unavailable")
    monkeypatch.setattr(prepare_release, "urlopen", unavailable)
    with pytest.raises(URLError):
        prepare_release.main()
    assert path.read_text(encoding="utf-8") == original


def test_dry_run_does_not_modify_source_or_github_outputs(tmp_path, monkeypatch, capsys):
    path = tmp_path / "__init__.py"
    path.write_text('__version__ = "0.1.0"\n', encoding="utf-8")
    output = tmp_path / "outputs"
    monkeypatch.setattr(prepare_release, "VERSION_FILE", path)
    monkeypatch.setattr(prepare_release, "published_versions", lambda: ["0.1.0"])
    monkeypatch.setattr("sys.argv", ["prepare_release.py", "--dry-run"])
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    prepare_release.main()
    assert prepare_release.source_version(path) == "0.1.0"
    assert not output.exists()
    assert capsys.readouterr().out.strip() == "0.1.1"


def test_release_stamps_source_and_exports_selected_version(tmp_path, monkeypatch):
    path = tmp_path / "__init__.py"
    path.write_text('__version__ = "0.1.0"\n', encoding="utf-8")
    output = tmp_path / "outputs"
    monkeypatch.setattr(prepare_release, "VERSION_FILE", path)
    monkeypatch.setattr(prepare_release, "published_versions", lambda: ["0.1.0"])
    monkeypatch.setattr("sys.argv", ["prepare_release.py"])
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    prepare_release.main()
    assert prepare_release.source_version(path) == "0.1.1"
    assert output.read_text(encoding="utf-8") == "version=0.1.1\n"
