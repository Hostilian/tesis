"""CLI: link laboratory soil results to Sentinel-2 bare-soil reflectance.

Commands (run from the repository root):

  # 1. Proof the method behaves, on SYNTHETIC data (labelled as such):
  #    a planted signal must be found; pure noise, unrelated smooth maps and a
  #    shared regional trend must NOT be reported as a signal.
  python pipeline/run_soil_link.py demo --out out/soil_demo.json --seeds 5

  # 2. How many lab samples to collect for a correlation of r = 0.3, testing
  #    3 properties, if only 1 in 3 samples has bare-soil imagery?
  python pipeline/run_soil_link.py power --r 0.3 --n-tests 3 --bare-share 0.33

  # 3. Real data: satellite features per lab sample (needs internet).
  #    samples.csv: sample_id, lat, lon, date (YYYY-MM-DD), then one column per
  #    lab property (soc_g_kg, clay_pct, ...). depth_cm, method, unit, lab and
  #    notes columns are kept as metadata. Keep private lab files OUTSIDE this
  #    repository.
  python pipeline/run_soil_link.py features --samples /private/samples.csv \
      --out /private/features.csv --workers 8

  # 4. Real data: test every lab property.
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


def _jsonable(o):
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    raise TypeError(type(o))


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, indent=2, allow_nan=True, default=_jsonable) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def cmd_demo(args: argparse.Namespace) -> int:
    report = {
        "data_status": "synthetic_demonstration",
        "note": "Fake data. Checks that the method finds a planted signal and does "
        "not report one for noise, unrelated smooth maps or a shared regional "
        "trend. Not evidence about real soil.",
        "scenarios": {},
    }
    all_ok = True
    for sc in sl.SCENARIOS:
        verdicts = []
        for seed in range(args.seeds):
            X, t, lat, lon = sl.synthetic_dataset(n=args.n, seed=seed, scenario=sc)
            g = sl.spatial_blocks(lat, lon, args.block_km)
            r = sl.evaluate_property(
                X,
                t["soc_g_kg"],
                g,
                sl.FEATURE_NAMES,
                lat=lat,
                lon=lon,
                n_permutations=args.permutations,
                seed=seed,
                models=sl.make_models(seed, fast=True),
            )
            verdicts.append(r["verdict"])
        hits = sum(v == sl.EXPECTED[sc] for v in verdicts)
        ok = hits == len(verdicts)
        all_ok &= ok
        report["scenarios"][sc] = {
            "expected": sl.EXPECTED[sc],
            "verdicts": verdicts,
            "correct": hits,
            "runs": len(verdicts),
        }
        print(
            f"{sc}: {hits}/{len(verdicts)} as expected ({sl.EXPECTED[sc]})", flush=True
        )
    report["all_as_expected"] = all_ok
    _write_json(Path(args.out), report)
    print("demo check:", "PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1


def cmd_power(args: argparse.Namespace) -> int:
    for r in args.r:
        n = sl.samples_needed(
            r, args.alpha, args.power, args.n_tests, args.bare_share, args.design_effect
        )
        print(
            f"r = {r}: collect {n} lab samples "
            f"(alpha {args.alpha} over {args.n_tests} test(s), power {args.power}, "
            f"bare-soil share {args.bare_share}, design effect {args.design_effect})"
        )
    print("Planning numbers only; they assume samples are otherwise independent.")
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
    fields: list[str] = []
    for r in rows:
        fields += [k for k in r if k not in fields]
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    have = sum(1 for r in rows if not math.isnan(r["red"]))
    print(
        f"{have}/{len(rows)} samples have bare-soil features; {time.time() - t0:.0f} s -> {out}"
    )
    return 0


def _f(v: str | None) -> float:
    try:
        return float(v) if v not in ("", None) else math.nan
    except ValueError:
        return math.nan


def cmd_evaluate(args: argparse.Namespace) -> int:
    samples = {s.sample_id: s for s in sl.read_samples(Path(args.samples))}
    with open(args.features, newline="", encoding="utf-8") as fh:
        feats = {r["sample_id"]: r for r in csv.DictReader(fh)}
    ids = [i for i in samples if i in feats]
    names = list(sl.FEATURE_NAMES)
    terrain_cov = {}
    if not args.no_terrain:
        for k in sl.TERRAIN_NAMES:
            cov = (
                float(np.mean([np.isfinite(_f(feats[i].get(k))) for i in ids]))
                if ids
                else 0.0
            )
            terrain_cov[k] = cov
            if cov >= 0.9:  # otherwise terrain gaps would silently drop samples
                names.append(k)
    X = np.asarray([[_f(feats[i].get(k)) for k in names] for i in ids])
    lat = np.asarray([samples[i].lat for i in ids])
    lon = np.asarray([samples[i].lon for i in ids])
    spectral_ok = np.isfinite(X).all(axis=1) if len(ids) else np.zeros(0, bool)
    targets = args.targets or sl.iter_targets(samples.values())

    report: dict = {
        "data_status": "observation_derived_result",
        "privacy": "Aggregated metrics only. No coordinates or sample ids are written.",
        "n_samples_in_csv": len(samples),
        "n_samples_with_feature_row": len(ids),
        "n_samples_with_all_features": int(spectral_ok.sum()),
        "features_used": names,
        "terrain_coverage": terrain_cov,
        "environment": cs.environment_versions(),
        "properties": {},
    }
    pvals = {}
    for t in targets:
        y = np.asarray([samples[i].values.get(t, np.nan) for i in ids], float)
        fin = np.isfinite(y)
        block_km, rng_km = args.block_km, math.nan
        if args.block_km <= 0:  # auto: at least the empirical range of y
            rng_km = sl.empirical_range_km(lat[fin], lon[fin], y[fin])
            block_km = max(5.0, rng_km) if math.isfinite(rng_km) else 10.0
        groups = sl.spatial_blocks(lat, lon, block_km)
        res = sl.evaluate_property(
            X,
            y,
            groups,
            names,
            lat=lat,
            lon=lon,
            n_permutations=args.permutations,
            seed=args.seed,
        )
        res["block_km"] = block_km
        res["empirical_range_km"] = rng_km
        res["n_censored_values"] = sum(t in samples[i].censored for i in ids)
        res["n_missing_value"] = int(np.sum(~fin))
        report["properties"][t] = res
        if res["status"] == "ok":
            loc = res["location_check"]
            pvals[t] = res["permutation"]["p_value"]
            b = res["best_model"]
            print(
                f"{t}: n={res['n']} block {block_km:.1f} km, {b} R2={res['models'][b]['r2']:.3f}, "
                f"beyond trend R2={loc.get('detrended_r2_from_spectra', float('nan')):.3f}, "
                f"p={pvals[t]:.3f} -> {res['verdict']}"
            )
        else:
            print(f"{t}: {res['status']} (n={res['n']})")
    if pvals:
        q = sl.fdr_bh(list(pvals.values()))
        for t, qi in zip(pvals, q):
            report["properties"][t]["q_across_properties"] = float(qi)
            if (
                qi > 0.05
                and report["properties"][t]["verdict"] == "signal_above_chance"
            ):
                report["properties"][t][
                    "verdict"
                ] = "no_evidence_after_multiple_testing"
    if spectral_ok.sum() >= 20:
        Xo = X[spectral_ok]
        aoa = sl.area_of_applicability(
            Xo, Xo, sl.spatial_blocks(lat[spectral_ok], lon[spectral_ok], 10.0)
        )
        report["area_of_applicability"] = {
            "di_threshold": aoa["threshold"],
            "note": "Call area_of_applicability() with the features of new places; "
            "predictions where DI > threshold must not be used.",
        }
    _write_json(Path(args.out), report)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("demo", help="synthetic checks that the method behaves")
    d.add_argument("--out", default="out/soil_demo.json")
    d.add_argument("--n", type=int, default=200)
    d.add_argument("--seeds", type=int, default=3)
    d.add_argument("--permutations", type=int, default=19)
    d.add_argument("--block-km", type=float, default=5.0)
    d.set_defaults(fn=cmd_demo)

    p = sub.add_parser("power", help="lab samples to collect for a given correlation")
    p.add_argument("--r", type=float, nargs="+", default=[0.2, 0.3, 0.4, 0.5])
    p.add_argument("--alpha", type=float, default=0.05)
    p.add_argument("--power", type=float, default=0.8)
    p.add_argument("--n-tests", type=int, default=1, help="lab properties tested")
    p.add_argument(
        "--bare-share",
        type=float,
        default=1.0,
        help="expected share with bare-soil imagery",
    )
    p.add_argument(
        "--design-effect", type=float, default=1.0, help=">1 for clustered sampling"
    )
    p.set_defaults(fn=cmd_power)

    f = sub.add_parser("features", help="Sentinel-2 bare-soil features per lab sample")
    f.add_argument("--samples", required=True)
    f.add_argument("--out", required=True)
    f.add_argument(
        "--window-days",
        type=int,
        default=365,
        help="search +- this many days around each sampling date",
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
    e.add_argument(
        "--block-km",
        type=float,
        default=0.0,
        help="CV block size; 0 = auto from the variogram",
    )
    e.add_argument("--permutations", type=int, default=199)
    e.add_argument("--seed", type=int, default=0)
    e.add_argument("--no-terrain", action="store_true", help="spectra only")
    e.set_defaults(fn=cmd_evaluate)

    args = ap.parse_args(argv)
    return int(args.fn(args))


if __name__ == "__main__":
    raise SystemExit(main())
