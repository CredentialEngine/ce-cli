# CI/CD

## CI pipeline

The CI pipeline runs automatically on every push to `main` and on every pull request targeting `main`.

**What it does:**
- Sets up Python 3.13
- Installs `tox`
- Runs unit tests via `tox -e unit`

Integration tests (those marked `@pytest.mark.integration`) are excluded from CI because they require a live API environment.

To run tests locally:
```
pip install tox
tox -e unit
```

## Release pipeline

Releases are triggered manually via **Actions → Release → Run workflow** in GitHub.

**Version format:** `YYYY.MM.DD.<run_number>` — for example, `2026.04.15.42`

The version is auto-generated from the date and the pipeline run number. There is no version field to manually edit and no tags to push.

**What the pipeline does:**
1. Generates the version from the current date and run number
2. Runs unit tests — if they fail, the release is aborted
3. Builds the package (`.whl` and `.tar.gz`) with the generated version embedded
4. Creates a GitHub Release tagged `v<version>` with both files attached and auto-generated release notes

**How to cut a release:**

Go to the repository on GitHub → Actions → Release → Run workflow → Run workflow.

That's it. The pipeline takes care of the rest.
