# Integrated thesis: Windows regression test evidence (2026-11-23)

**Scope:** Authorized local Windows checkout of `Hostilian/tesis`, branch `operation/thesis-convergence-integrated-20261122` at `e7fcd62a9593254c562ba0281117078834ab0565`. This is a software regression check, **not** independent scientific anomaly/event validation.

## Actual observations

1. Test environment: Windows, Python 3.12.5, pytest 9.2.0, FastAPI 0.165.0, Starlette 1.10.0. The pre-existing local virtual environment lacked `httpx2`; initial `pytest -q` **stopped during collection**, before a valid suite result.
2. Starlette's official TestClient instructions require `httpx2`: https://starlette.dev/testclient/ . Installed `httpx2==2.16.2` into the existing local virtual environment, with pip exit code 0. The requirement was added to `pipeline/requirements-dev.txt` on this isolated review branch. The already-listed `httpx` package is not an equivalent replacement.
3. The next run completed with **98 passed, 4 errors**; all four errors were fixture setup permission failures in the Windows default `Temp/pytest-of-...` directory. The test implementations did not fail, but the suite was not fully passing.
4. The final rerun, assigning a writable local pytest base directory, returned **102 passed in 20.59 seconds, exit code 0**.

## Reproduction

Use the repository's development requirements in a compatible Python environment. On a Windows machine where pytest's default base temp directory is inaccessible, set a new writable directory outside protected folders:

```powershell
python -m pip install -r pipeline/requirements-dev.txt
python -m pytest -q --basetemp="$env:USERPROFILE\Documents\thesis-pytest-isolated"
```

The command above is a suggested reproduction command; the recorded run used the same `--basetemp` mechanism with an existing local venv and a different isolated directory. Do not claim the command above was independently run.

## Interpretation and exclusions

- **Passed:** 102 Python automated checks on the exact integrated tree before this dependency-documentation patch.
- **Not run:** full installation of all pinned production dependencies in a new clean environment, GitHub Actions on this new review-branch commit, headless visual browser tests, complete manuscript PDF regeneration, and end-to-end remote satellite-provider acquisition in this session.
- **Not established:** independent environmental event labels, spatial/temporal out-of-sample scientific validation, detection precision/recall/F1, agricultural interpretation, economic causality, or supervisor approval.
- **Preservation:** the public `main` site and default satellite view were not changed by these test-repair commits.

Log files from these three test runs remain on the authorized Windows computer. No credentials, commercial farm data, or private academic files were committed.
