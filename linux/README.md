# Running the thesis pipeline on a Linux machine

This folder lets anyone rerun the thesis evidence on a Linux computer. You need no API keys, no accounts and no admin rights.

## What it needs

Every number below was measured on 27 November 2026 unless it says "estimate".

| | Minimum | Comfortable | Why |
|---|---|---|---|
| Operating system | any 64-bit Linux with Python 3.10+, or Docker | Ubuntu 22.04/24.04, Python 3.12 | The published runs used Python 3.12.5 |
| CPU | 2 cores | 8–16 cores | Model checks with many repetitions use every core |
| RAM | 8 GB | 16–32 GB | Estimate; GitHub's Linux job will record the real peak (`Maximum resident`) |
| Free disk | 5 GB | 20–50 GB | Python environment about 1.5 GB (estimate); case-study outputs 14 MB (measured) |
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
bash linux/setup.sh              # 2. private Python environment in .venv-linux (about 5 min)
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
- `.github/workflows/linux-run-kit.yml` runs the same three steps on a clean Ubuntu 24.04 machine at GitHub after each push. It has not run yet; check its result before relying on Linux.
