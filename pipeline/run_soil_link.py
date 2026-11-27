"""CLI: link laboratory soil results to Sentinel-2 bare-soil reflectance.

Commands (run from the repository root):

  # 1. Proof the method works, on SYNTHETIC data (labelled as such):
  #    a planted signal must be found, pure noise must NOT be.
  python pipeline/run_soil_link.py demo --out out/soil_demo.json

  # 2. How many lab samples are needed to detect a correlation of r = 0.3?
  python pipeline/run_soil_link.py power --r 0.3

  # 3. Real data: build satellite features for each lab sample (needs internet).
  #    samples.csv columns: sample_id, lat, lon, date (YYYY-MM-DD), then one
  #    column per lab property (e.g. soc_g_kg, clay_pct, ph). Keep private
  #    lab files OUTSIDE this repository.
  python pipeline/run_soil_link.py features --samples /private/samples.csv --out /private/features.csv

  # 4. Real data: test every lab property against the features.
  python pipeline/run_soil_link.py evaluate --samples /private/samples.csv \
      --features /private/features.csv --out /private/soil_report.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from pipeline.src import case_study as cs  # noqa: E402
from pipeline.src import soil_link as sl  # noqa: E402


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, allow_nan=True) + "\n", encoding="utf-8", newline="\n"
    )


def cmd_demo(args: argparse.Namespace) -> int:
    report = {
        "data_status": "synthetic_demonstration",
        "note": "Fake data. Shows the method finds a planted signal and does not invent one. Not evidence about real soil.",
        "cases": {},
    }
    for label, signal in (("planted_signal", 1.0), ("no_signal", 0.0)):
        X, targets, lat, lon = sl.synthetic_dataset(
            n=args.n, signal=signal, seed=args.seed
        )
        groups = sl.spatial_blocks(lat, lon, args.block_km)
        res = sl.evaluate_property(
            X,
            targets["soc_g_kg"],
            groups,
            sl.FEATURE_NAMES,
            n_permutations=args.permutations,
            seed=args.seed,
        )
        res.pop("screen", None)
        report["cases"][label] = res
        print(
            f"{label}: best={res['best_model']} r2={res['models'][res['best_model']]['r2']:.3f} p={res['permutation']['p_value']:.3f} -> {res['verdict']}"
        )
    _write_json(Path(args.out), report)
    ok = (
        report["cases"]["planted_signal"]["verdict"] == "signal_above_chance"
        and report["cases"]["no_signal"]["verdict"] == "no_evidence_of_signal"
    )
    print("demo check:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def cmd_power(args: argparse.Namespace) -> int:
    for r in args.r:
        print(
            f"r = {r}: {sl.samples_needed(r, args.alpha, args.power)} samples (alpha {args.alpha}, power {args.power})"
        )
    return 0


def cmd_features(args: argparse.Namespace) -> int:
    samples = sl.read_samples(Path(args.samples))
    t0 = time.time()
    rows = sl.extract_features(
        samples,
        window_days=args.window_days,
        max_cloud=args.max_cloud,
        max_scenes=args.max_scenes,
        workers=args.workers,
        ndvi_max=args.ndvi_max,
        nbr2_max=args.nbr2_max,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    have = sum(1 for r in rows if not math.isnan(r["red"]))
    print(
        f"{have}/{len(rows)} samples have bare-soil features; {time.time() - t0:.0f} s -> {out}"
    )
    return 0


def cmd_evaluate(args: argparse.Namespace) -> int:
    samples = {s.sample_id: s for s in sl.read_samples(Path(args.samples))}
    with open(args.features, newline="", encoding="utf-8") as fh:
        feats = {r["sample_id"]: r for r in csv.DictReader(fh)}
    ids = [i for i in samples if i in feats]
    first = next(iter(feats.values()), {})
    names = list(sl.FEATURE_NAMES) + [
        k for k in sl.TERRAIN_NAMES if not args.no_terrain and k in first
    ]
    X = np.asarray(
        [
            [
                float(feats[i][k])
                if feats[i].get(k) not in ("", "nan", None)
                else np.nan
                for k in names
            ]
            for i in ids
        ]
    )
    lat = [samples[i].lat for i in ids]
    lon = [samples[i].lon for i in ids]
    groups = sl.spatial_blocks(lat, lon, args.block_km)
    targets = args.targets or sl.iter_targets(samples.values())
    report = {
        "data_status": "observation_derived_result",
        "privacy": "Aggregated metrics only. No coordinates or sample ids are written.",
        "n_samples_matched": len(ids),
        "block_km": args.block_km,
        "environment": cs.environment_versions(),
        "properties": {},
    }
    for t in targets:
        y = np.asarray([samples[i].values.get(t, np.nan) for i in ids], float)
        res = sl.evaluate_property(
            X, y, groups, names, n_permutations=args.permutations, seed=args.seed
        )
        report["properties"][t] = res
        if res["status"] == "ok":
            b = res["best_model"]
            print(
                f"{t}: n={res['n']} {b} r2={res['models'][b]['r2']:.3f} p={res['permutation']['p_value']:.3f} -> {res['verdict']}"
            )
        else:
            print(f"{t}: {res['status']} (n={res['n']})")
    _write_json(Path(args.out), report)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("demo", help="synthetic proof that the method works")
    d.add_argument("--out", default="out/soil_demo.json")
    d.add_argument("--n", type=int, default=200)
    d.add_argument("--seed", type=int, default=0)
    d.add_argument("--permutations", type=int, default=99)
    d.add_argument("--block-km", type=float, default=5.0)
    d.set_defaults(fn=cmd_demo)

    p = sub.add_parser("power", help="lab samples needed for a given correlation")
    p.add_argument("--r", type=float, nargs="+", default=[0.2, 0.3, 0.4, 0.5])
    p.add_argument("--alpha", type=float, default=0.05)
    p.add_argument("--power", type=float, default=0.8)
    p.set_defaults(fn=cmd_power)

    f = sub.add_parser("features", help="Sentinel-2 bare-soil features per lab sample")
    f.add_argument("--samples", required=True)
    f.add_argument("--out", required=True)
    f.add_argument(
        "--window-days",
        type=int,
        default=365,
        help="search +- this many days around each sampling date (soil carbon and clay change slowly)",
    )
    f.add_argument("--max-cloud", type=float, default=20.0)
    f.add_argument("--max-scenes", type=int, default=12)
    f.add_argument(
        "--workers", type=int, default=4, help="samples processed in parallel"
    )
    f.add_argument("--ndvi-max", type=float, default=sl.NDVI_MAX)
    f.add_argument("--nbr2-max", type=float, default=sl.NBR2_MAX)
    f.set_defaults(fn=cmd_features)

    e = sub.add_parser("evaluate", help="test each lab property against the features")
    e.add_argument("--samples", required=True)
    e.add_argument("--features", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--targets", nargs="*")
    e.add_argument("--block-km", type=float, default=5.0)
    e.add_argument("--permutations", type=int, default=199)
    e.add_argument("--seed", type=int, default=0)
    e.add_argument("--no-terrain", action="store_true", help="spectra only")
    e.set_defaults(fn=cmd_evaluate)

    args = ap.parse_args(argv)
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
