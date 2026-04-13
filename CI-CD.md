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

Releases are triggered by pushing a version tag to `main`.

**Tag format:** `vMAJOR.MINOR.PATCH` — for example, `v1.2.0`

The version number is read automatically from the git tag via `setuptools-scm` — there is no version field to manually edit.

**What the pipeline does:**
1. Runs unit tests — if they fail, the release is aborted
2. Builds the package (`.whl` and `.tar.gz`)
3. Creates a GitHub Release with both files attached and auto-generated release notes

**How to cut a release:**
```
git tag v1.2.0
git push origin v1.2.0
```

That's it. The pipeline takes care of the rest.
