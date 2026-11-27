# Running the thesis pipeline on a Linux machine

This folder lets anyone rerun the thesis evidence on a Linux computer. You need no API keys, no accounts and no admin rights.

## What it needs

Every number below was measured on 27 November 2026 unless it says "estimate".

| | Minimum | Comfortable | Why |
|---|---|---|---|
| Operating system | any 64-bit Linux with Python 3.12+, or Docker (the pinned rasterio 1.5.0 needs 3.12) | Ubuntu 22.04/24.04, Python 3.12 | The published runs used Python 3.12.5 |
| CPU | 2 cores | 8–16 cores | Model checks with many repetitions use every core |
| RAM | 4 GB | 16–32 GB | Tests + soil checks peaked at 198 MB on GitHub's Ubuntu 24.04 machine (27 Nov). A full case-study rerun and large soil sets need more |
| Free disk | 5 GB | 20–50 GB | Python environment 652 MB and case-study outputs 14 MB (both measured) |
| GPU | not needed | optional, only for later foundation-model tests | Nothing in the current pipeline uses a GPU |
| Network | outbound HTTPS to 4 public servers | same | Satellite images are read from public cloud storage |

**Why so little disk.** The pipeline never downloads whole satellite images; one Sentinel-2 scene is roughly 1 GB. It reads only the small window it needs from cloud-optimised GeoTIFFs. A 10 × 10 km study area or a 60 m box around a soil sample is a few megabytes per date.

**What limits the speed.** Download speed, not computing power.
- Each case study took about 2.3 minutes on a laptop (`runtime_seconds` 135.7 and 138.3 in the published manifests).
- Reading soil features took about 13 seconds per satellite date per sample, with 3 samples in parallel.

The four servers it must reach (checked by `check_machine.sh`):
- `earth-search.aws.element84.com` — Sentinel-2 catalogue (Element 84)
- `sentinel-cogs.s3.us-west-2.amazonaws.com` — the image files (AWS Open Data)
- `planetarycomputer.microsoft.com` — second provider, used for the cross-check
- `pypi.org` — Python packages, during setup only

## Three commands

```bash
bash linux/check_machine.sh      # 1. what this machine has; changes nothing
bash linux/setup.sh              # 2. private Python environment in .venv-linux (about 5 min; versions locked by linux/requirements-linux.lock)
bash linux/run_all.sh            # 3. tests + synthetic soil check (about 2 min)
bash linux/run_all.sh --full     #    or: also redo both case studies from live satellite data
```

Results go to `out/linux-<time>/SUMMARY.md` with one line per step (PASS/FAIL, seconds, exact command), plus a log file per step.

With Docker instead:

```bash
docker build -f linux/Dockerfile -t tesis-linux .
docker run --rm tesis-linux
```

## What `--full` proves

It re-downloads the same Sentinel-2 scenes (pinned by their catalogue IDs) and recomputes both Portuguese case studies, their robustness checks and the independent re-implementation. Afterwards `git diff --stat docs/case-study/data` should show changes only in run IDs, timestamps and environment fields. Any change in a number means the result is not reproducible, and that has to be investigated.

## Soil laboratory ↔ satellite link

See `pipeline/run_soil_link.py --help` and `docs/SOIL_LINK_PLAN.md`. Laboratory files with farm coordinates are private and must stay outside this repository; pass them in by path:

```bash
python pipeline/run_soil_link.py features --samples /private/samples.csv --out /private/features.csv --workers 8
python pipeline/run_soil_link.py evaluate --samples /private/samples.csv --features /private/features.csv --out /private/report.json
```

## Checked where

- `check_machine.sh`: run in Git Bash on the Windows laptop. It correctly reported 15 GB RAM, 15 GB free disk, an RTX 3060 GPU, all 4 servers reachable, and an old `python3` (3.9) on that path.
- All three scripts pass `bash -n` (syntax check).
- `.github/workflows/linux-run-kit.yml` ran the same three steps on a clean Ubuntu 24.04 machine at GitHub on 27 Nov 2026 (run 46006335625):
  - the machine check had 9 OK, 1 warning (RAM under 16 GB) and 0 failures;
  - the whole job took 65 s, and the tests plus soil checks inside it took 17 s;
  - peak memory was 198 MB.
- **Full rerun on Linux** (GitHub run 46027765446, 27 Nov 2026):
  - every step passed: both case studies from live satellite data, both robustness checks and both independent re-implementations;
  - 5 min 30 s wall time, 415 MB peak memory, 652 MB Python environment;
  - **every published number reproduced exactly**. The only changed result line is a map-overlay longitude: −7.924011040981401 on Windows, −7.924011040981397 on Linux. That is 4 × 10⁻¹⁵ degrees, below a nanometre, from floating-point rounding in the coordinate library.
- To repeat it: Actions tab → "Linux run kit" → Run workflow → tick "full".
