#!/usr/bin/env bash
# Re-runs the evidence chain on Linux and writes a summary.
#   bash linux/run_all.sh          # tests + synthetic soil check (no satellite download)
#   bash linux/run_all.sh --full   # also re-runs both Portugal case studies,
#                                  # the robustness checks and the independent check
# Logs go to out/linux-<timestamp>/. Published files in docs/ change only with
# --full, exactly as on Windows (they are hashed in their manifests).
set -uo pipefail
cd "$(dirname "$0")/.."
# shellcheck disable=SC1091
. .venv-linux/bin/activate
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
OUT="out/linux-$STAMP"
mkdir -p "$OUT"
SUMMARY="$OUT/SUMMARY.md"
status=0

step() {
  local name="$1"; shift
  local t0 r
  t0=$(date +%s)
  echo "== $name"
  if "$@" > "$OUT/$name.log" 2>&1; then r=PASS; else r=FAIL; status=1; fi
  echo "| $name | $r | $(( $(date +%s) - t0 )) s | \`$*\` |" >> "$SUMMARY"
  tail -3 "$OUT/$name.log"
}

{
  echo "# Linux run $STAMP"
  echo
  echo "- commit: $(git rev-parse HEAD 2>/dev/null || echo 'not a git checkout')"
  echo "- machine: $(uname -srm), $(nproc) cores, $(awk '/MemTotal/ {printf "%.1f GB", $2/1048576}' /proc/meminfo)"
  echo "- python: $(python -V 2>&1)"
  echo
  echo "| step | result | time | command |"
  echo "|---|---|---|---|"
} > "$SUMMARY"

step tests python -m pytest -q -p no:cacheprovider \
  pipeline/tests/test_case_study.py pipeline/tests/test_case_study_properties.py \
  pipeline/tests/test_robustness.py pipeline/tests/test_provider_pc.py \
  pipeline/tests/test_threshold_simulation.py pipeline/tests/test_formal_spec.py \
  pipeline/tests/test_soil_link.py
step soil_demo python pipeline/run_soil_link.py demo --out "$OUT/soil_demo.json"
step soil_power python pipeline/run_soil_link.py power

if [ "${1:-}" = "--full" ]; then
  for c in alqueva_olive neves_corvo_mine; do
    step "case_$c" python pipeline/run_case_study.py run "pipeline/case_studies/$c.json"
  done
  # Exact commands recorded in docs/case-study/data/*/robustness.json (manifest.command)
  step robustness_alqueva_olive python pipeline/run_robustness.py \
    pipeline/case_studies/alqueva_olive.json \
    --alt-before S2B_29SNC_20180823_1_L2A --alt-after S2A_29SNC_20250823_0_L2A \
    --alt-control-before S2A_29SNC_20250803_0_L2A
  step robustness_neves_corvo_mine python pipeline/run_robustness.py \
    pipeline/case_studies/neves_corvo_mine.json \
    --alt-before S2B_29SNB_20180823_1_L2A --alt-after S2B_29SNB_20250826_0_L2A \
    --alt-control-before S2A_29SNB_20250803_1_L2A --fine-grid 0.01 0.20 0.01
  for c in alqueva_olive neves_corvo_mine; do
    step "independent_$c" python pipeline/verify_independent.py "pipeline/case_studies/$c.json"
  done
  {
    echo
    echo "Check: \`git diff --stat docs/case-study/data\` should show only run ids, timestamps and environment fields."
    git diff --stat docs/case-study/data 2>/dev/null || true
    echo
    echo "Changed lines in results.json, ignoring run ids, times, paths and versions"
    echo "(empty = every published number reproduced exactly):"
    echo '```'
    git diff -U0 -- 'docs/case-study/data/*/results.json' 2>/dev/null \
      | grep -E '^[-+] ' \
      | grep -v -E 'run_id|_utc|created|generated|timestamp|"python"|platform|commit|"path"|href|version' \
      | head -40 || true
    echo '```'
  } >> "$SUMMARY"
fi

echo
cat "$SUMMARY"
exit $status
