"""Shared test fixtures.

Some tests exercise code that writes caches into the tracked ``docs/data``
folder (World Bank cache refresh, financial webhook feed). Running the suite
must not leave the published data modified, so every file under
``docs/data`` is snapshotted before the session and restored afterwards;
files created during the session are removed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PROTECTED = REPO / "docs" / "data"


@pytest.fixture(scope="session", autouse=True)
def _restore_published_data():
    before = {p: p.read_bytes() for p in PROTECTED.rglob("*") if p.is_file()}
    yield
    for p in PROTECTED.rglob("*"):
        if p.is_file() and p not in before:
            p.unlink()
    for p, data in before.items():
        if not p.exists() or p.read_bytes() != data:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
