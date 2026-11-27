"""Simulation check of the control_p99 threshold rule (synthetic noise only).

Claim tested: when the threshold is chosen from one noise draw, the fraction of
pixels flagged in a fresh draw of the same noise stays near or below the
nominal 1 %. This is a property of the rule under Gaussian noise. It says
nothing about real satellite noise, which is checked by the case-study runs.
"""

from __future__ import annotations

import numpy as np

from pipeline.src import case_study as cs

GRID = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.6, 1.0]


def test_control_p99_rule_keeps_false_alarms_low_under_gaussian_noise():
    rng = np.random.default_rng(42)
    rates = []
    for _ in range(60):
        sigma = rng.uniform(0.02, 0.12)
        ctrl = rng.normal(0, sigma, 20000).astype("float32")
        t, _ = cs.resolve_threshold("control_p99", GRID, ctrl)
        fresh = rng.normal(0, sigma, 20000)
        rates.append((np.abs(fresh) > t).mean())
    rates = np.array(rates)
    # Nominal target is 1 %; the rule is conservative, so the mean sits well below it.
    assert rates.mean() < 0.01
    assert np.percentile(rates, 95) < 0.015
