#!/usr/bin/env bash
# One-time setup: a private Python environment inside the project folder.
# Needs no admin rights. Usage (from the project folder): bash linux/setup.sh
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"
"$PY" -m venv .venv-linux
# shellcheck disable=SC1091
. .venv-linux/bin/activate
python -m pip install --upgrade pip -q
# The lock pins every transitive package to the versions behind the published results.
python -m pip install -r linux/requirements-linux.txt -c linux/requirements-linux.lock -q
python -c "import rasterio, pystac_client, sklearn; print('environment ready: rasterio', rasterio.__version__, '| scikit-learn', sklearn.__version__)"
