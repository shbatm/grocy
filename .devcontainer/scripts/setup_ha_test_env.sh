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
source "${VENV_DIR}/bin/activate"

python -m pip install -U pip setuptools wheel


echo "Installing Home Assistant from PyPI (pre-release allowed) into venv..."
# Try to install the latest pre-release (beta) of homeassistant with tests extras
set +e
python -m pip install --pre "homeassistant[tests]"
if [ $? -ne 0 ]; then
    echo "Failed to install homeassistant[tests], trying homeassistant[dev] then homeassistant"
    python -m pip install --pre "homeassistant[dev]" || python -m pip install --pre "homeassistant"
fi
set -e

cd "${WORKSPACE_DIR}"

# Install integration-specific requirements from manifest.json
if command -v jq >/dev/null 2>&1; then
    for req in $(jq -c -r '.requirements | .[]' custom_components/grocy/manifest.json); do
        python -m pip install "$req"
    done
fi

# Ensure pytest available
python -m pip install -U pytest pytest-asyncio

echo "Setup complete. Activate the venv with: source ${VENV_DIR}/bin/activate"
