# Automatic PyPI Releases

## What The Workflow Does

`.github/workflows/ci.yml` runs on branch pushes, pull requests, and manual dispatch.
Every run tests Windows/Linux across Python 3.11, 3.12, and 3.13. If all tests pass,
it builds a wheel and source archive, checks them with Twine, and installs the wheel
in a fresh environment outside the source directory to verify both CLI entrypoints
and the installed version metadata. Distributions are retained as Actions artifacts
for seven days.

On `main` in `saurabh-1008/api-stress-lab`, successful push/manual runs also publish
to PyPI. Pull requests, tags, other branches, and forks never publish. The publishing
job downloads the verified build artifact; it does not rebuild or check out code.
Only that job receives `id-token: write` for PyPI's short-lived OIDC authentication.

Every push to `main`, including documentation-only changes, is a release candidate.
Batch development on branches and merge when it is ready for users.

## One-Time Setup

1. In the GitHub repository, open Settings > Environments and create `pypi`.
   Restrict its deployment branches to `main`. Leave required-reviewer approvals
   disabled if publishing should be fully automatic.
2. In PyPI, manage the existing `api-stress-lab` project and open Publishing.
   Add a GitHub Trusted Publisher with these exact fields:

| PyPI field | Value |
| --- | --- |
| Owner | `saurabh-1008` |
| Repository | `api-stress-lab` |
| Workflow filename | `ci.yml` |
| Environment name | `pypi` |

3. Commit and push the workflow changes. Make sure Actions is enabled for the
   repository. Open Actions > CI and Publish to watch tests, build, and publishing.

No `PYPI_API_TOKEN` or other publishing secret is needed. Do not put tokens in
source files. Configuring a Trusted Publisher is an account-level setup action;
adding a YAML file alone does not configure PyPI.

Official instructions: [PyPI Trusted Publisher setup](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).

## Automatic Versions

`api_stress_lab/__init__.py` is the single source of the package's baseline version.
`pyproject.toml` reads it through setuptools dynamic metadata.

Before a publishable build, `scripts/prepare_release.py` reads release numbers from
the PyPI JSON API and chooses the next stable patch number. If the source baseline
is higher than all published stable versions, it uses that baseline instead.
Otherwise, a latest version of `0.1.0` becomes `0.1.1`, then `0.1.2`, and so on.
Existing yanked versions count as used. Prerelease/dev versions are not the stable
release baseline. Network failures or malformed responses stop the build rather
than guessing a version.

CI stamps the chosen version into its own checkout before building. Both wheel
metadata and `api_stress_lab.__version__` therefore agree. The source repository is
not modified by the workflow, and local editable installs keep the source baseline.
To intentionally start `0.2.0`, for example, set that baseline in `__init__.py` when
the latest stable release is still below `0.2.0`.

Preview the next version locally without changing files:

```bash
python -m pip install -e ".[dev]"
python scripts/prepare_release.py --dry-run
```

Workflow concurrency serializes runs on the same branch through version selection
and publication. GitHub may replace an older pending run with the latest push;
an active release is not canceled. This delivers the latest queued changes without
publishing two CI builds under the same version. Avoid manual uploads in parallel
with the automated publisher.

## Retries And Troubleshooting

- For failed tests, fix the failure on a branch and merge; no package is published.
- For an OIDC/403 error, confirm the owner, repo, workflow filename, and environment
  match the Trusted Publisher, and the `pypi` environment permits `main`.
- After fixing account setup, choose Actions > CI and Publish > Run workflow and
  select `main` to retry. A manual run on another branch only runs checks.
- Re-running a failed publishing job reuses its build artifact. Already-uploaded
  distributions are skipped, allowing a partially completed upload to finish.
- If PyPI already has a conflicting version from a manual upload, start a new full
  workflow on `main` to select a fresh version.
- If the artifact has expired, start a new full workflow to rebuild.

After publishing, install with `python -m pip install --upgrade api-stress-lab` and
inspect the release at [PyPI](https://pypi.org/project/api-stress-lab/). The workflow
does not automatically create Git tags or GitHub Release pages.
