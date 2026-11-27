#!/usr/bin/env bash
# Prints what this Linux machine has and whether it is enough.
# Read-only: installs nothing and writes nothing except to the terminal.
# Usage: bash linux/check_machine.sh [work_dir]
set -u
WORK="${1:-$PWD}"
ok=0; warn=0; fail=0
pass() { echo "  OK    $*"; ok=$((ok+1)); }
note() { echo "  WARN  $*"; warn=$((warn+1)); }
bad()  { echo "  FAIL  $*"; fail=$((fail+1)); }

echo "== System"
echo "  $(uname -srm)"
if [ -r /etc/os-release ]; then . /etc/os-release; echo "  ${PRETTY_NAME:-unknown}"; fi

echo "== CPU"
cores=$(nproc 2>/dev/null || echo 1)
echo "  $cores cores: $(grep -m1 'model name' /proc/cpuinfo 2>/dev/null | cut -d: -f2)"
if [ "$cores" -ge 4 ]; then pass "4+ cores"; else note "fewer than 4 cores: everything runs, just slower"; fi

echo "== Memory"
mem_gb=$(awk '/MemTotal/ {printf "%d", $2/1024/1024}' /proc/meminfo 2>/dev/null || echo 0)
echo "  ${mem_gb} GB RAM"
if [ "$mem_gb" -ge 16 ]; then pass "16+ GB RAM"
elif [ "$mem_gb" -ge 8 ]; then note "8-15 GB RAM: enough for the case study and a few thousand soil samples"
else bad "under 8 GB RAM: the 10x10 km case study needs a few GB at peak"; fi

echo "== Disk (free space where the work runs: $WORK)"
free_gb=$(df -Pk "$WORK" 2>/dev/null | awk 'NR==2 {printf "%d", $4/1024/1024}')
echo "  ${free_gb:-?} GB free"
if [ "${free_gb:-0}" -ge 20 ]; then pass "20+ GB free"
elif [ "${free_gb:-0}" -ge 5 ]; then note "5-19 GB free: enough for code, environment and outputs; not for large image caches"
else bad "under 5 GB free: the Python environment alone needs about 1.5 GB"; fi

echo "== GPU (optional; only for later foundation-model experiments)"
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | sed 's/^/  /'
  pass "NVIDIA GPU present"
else
  echo "  none found: fine, nothing in the current pipeline needs a GPU"
fi

echo "== Software"
if command -v python3 >/dev/null 2>&1; then
  v=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')
  echo "  python3 $v"
  case "$v" in
    3.1[0-1]) note "Python $v works for most parts; the published runs used 3.12" ;;
    3.1[2-9]) pass "Python $v" ;;
    *) bad "Python $v is too old; need 3.10+ (3.12 recommended), or use Docker" ;;
  esac
  if python3 -c 'import venv, ensurepip' 2>/dev/null; then pass "python3 venv module"
  else bad "python3-venv missing (admin: apt install python3-venv), or use Docker"; fi
else
  bad "python3 not found"
fi
if command -v git >/dev/null 2>&1; then pass "git $(git --version | cut -d' ' -f3)"; else note "git missing: copy the project as a zip instead"; fi
if command -v docker >/dev/null 2>&1; then echo "  docker available (optional)"; else echo "  docker not installed (optional)"; fi

echo "== Network (public endpoints, no keys)"
for url in https://earth-search.aws.element84.com/v1 \
           https://planetarycomputer.microsoft.com/api/stac/v1 \
           https://sentinel-cogs.s3.us-west-2.amazonaws.com \
           https://pypi.org/simple/; do
  code=$(curl -s -o /dev/null -m 15 -w '%{http_code}' "$url" 2>/dev/null || echo 000)
  case "$code" in
    2*|3*|403) pass "$url ($code)" ;;
    *) bad "$url unreachable ($code): satellite data or packages cannot be downloaded" ;;
  esac
done
if [ -n "${HTTPS_PROXY:-${https_proxy:-}}" ]; then echo "  proxy in use: ${HTTPS_PROXY:-${https_proxy:-}}"; fi

echo
echo "Summary: $ok ok, $warn warnings, $fail failures"
[ "$fail" -eq 0 ]
