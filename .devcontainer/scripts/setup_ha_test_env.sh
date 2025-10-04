#!/usr/bin/env bash
set -euo pipefail

# Variables
HA_CORE_DIR="/workspaces/home-assistant-core"
WORKSPACE_DIR="/workspaces/grocy"
VENV_DIR="${WORKSPACE_DIR}/.venv"

echo "Setting up Home Assistant test environment..."

# Create venv
if [ ! -d "${VENV_DIR}" ]; then
    python3 -m venv "${VENV_DIR}"
fi
# Ensure venv has pip bootstrapped (Debian images may not include pip in venvs)
if [ ! -f "${VENV_DIR}/bin/pip" ]; then
    echo "Bootstrapping pip into venv..."
    # Try to use the venv python to run ensurepip; fall back to system python3
    "${VENV_DIR}/bin/python" -m ensurepip --upgrade 2>/dev/null || python3 -m ensurepip --upgrade 2>/dev/null || true
fi

source "${VENV_DIR}/bin/activate"

# Use the venv python explicitly to avoid PEP 668 / externally-managed-environment issues
VENV_PYTHON="${VENV_DIR}/bin/python"
${VENV_PYTHON} -m pip install -U pip setuptools wheel

export PIP_CACHE_DIR="/workspaces/.cache/pip"
WHEEL_DIR="/workspaces/.wheels"
mkdir -p "$PIP_CACHE_DIR" "$WHEEL_DIR"
echo "Using pip cache: $PIP_CACHE_DIR"

echo "Installing Home Assistant from PyPI (pre-release allowed) into venv..."
# Try to build a wheelhouse first (cached under $WHEEL_DIR) to speed up future builds
set +e
echo "Attempting to build wheelhouse for Home Assistant (cached at $WHEEL_DIR) -- this may take a while on first run..."
${VENV_PYTHON} -m pip wheel --wheel-dir "$WHEEL_DIR" --pre "homeassistant[tests]" || true
set -e

# If we have wheels, install from the wheelhouse (fast); otherwise install from PyPI (prefer binary)
if [ -n "$(ls -A "$WHEEL_DIR" 2>/dev/null)" ]; then
    echo "Found prebuilt wheels in $WHEEL_DIR, installing from wheelhouse..."
    ${VENV_PYTHON} -m pip install --no-index --find-links "$WHEEL_DIR" --pre "homeassistant[tests]"
else
    echo "No wheelhouse found, installing Home Assistant from PyPI (this may compile some wheels)..."
    ${VENV_PYTHON} -m pip install --pre --prefer-binary "homeassistant[tests]" || \
        (echo "Fallback: trying homeassistant[dev] then homeassistant" && ${VENV_PYTHON} -m pip install --pre "homeassistant[dev]" || ${VENV_PYTHON} -m pip install --pre "homeassistant")
fi

cd "${WORKSPACE_DIR}"

# Install integration-specific requirements from manifest.json
if command -v jq >/dev/null 2>&1; then
    for req in $(jq -c -r '.requirements | .[]' custom_components/grocy/manifest.json); do
    ${VENV_PYTHON} -m pip install "$req"
    done
fi

# Ensure pytest available
${VENV_PYTHON} -m pip install -U pytest pytest-asyncio

echo "Setup complete. Activate the venv with: source ${VENV_DIR}/bin/activate"
