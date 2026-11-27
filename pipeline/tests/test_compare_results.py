"""Tests for linux/compare_results.py (the reproduction check)."""

from __future__ import annotations

import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "compare_results", Path(__file__).resolve().parents[2] / "linux" / "compare_results.py"
)
cr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cr)


def test_rounding_between_operating_systems_is_ignored():
    # Real case: overlay longitude on Windows vs Linux (27 Nov 2026).
    assert list(cr.walk({"a": -7.924011040981401}, {"a": -7.924011040981397})) == []


def test_real_number_change_is_reported():
    assert list(cr.walk({"x": {"area_ha": 2260.19}}, {"x": {"area_ha": 2260.5}})) == [
        "/x/area_ha: 2260.19 -> 2260.5"
    ]


def test_ids_times_and_versions_are_ignored():
    a = {"run_id": "a", "created_utc": "t1", "environment": {"numpy": "1"}, "n": 3}
    b = {"run_id": "b", "created_utc": "t2", "environment": {"numpy": "2"}, "n": 3}
    assert list(cr.walk(a, b)) == []


def test_structure_changes_are_reported():
    assert list(cr.walk({"l": [1, 2]}, {"l": [1, 2, 3]})) == ["/l: list length 2 -> 3"]
    assert list(cr.walk({"a": 1}, {"a": 1, "b": 2})) == ["/b: present only in new file"]
    assert list(cr.walk({"flag": True}, {"flag": False})) == ["/flag: True -> False"]


def test_committed_outputs_currently_reproduce():
    assert cr.main() == 0
