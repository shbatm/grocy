#!/usr/bin/env bash
# Idempotent refresh helper for .homeassistant runtime folder.
# Use when you want to re-copy the default configuration or re-create the symlink.
set -euo pipefail
repo_root="$(cd "$(dirname "$0")/../" && pwd -P)"
cd "$repo_root"

echo "[refresh_homeassistant_runtime] repo_root=$repo_root"

if [ -d ".homeassistant" ]; then
  echo "[refresh_homeassistant_runtime] .homeassistant exists"
else
  echo "[refresh_homeassistant_runtime] .homeassistant missing, creating"
  mkdir -p .homeassistant
fi

# Copy configuration.yaml only if upstream devcontainer copy exists
if [ -f ".devcontainer/configuration.yaml" ]; then
  echo "[refresh_homeassistant_runtime] copying .devcontainer/configuration.yaml -> .homeassistant/configuration.yaml"
  cp -n .devcontainer/configuration.yaml .homeassistant/configuration.yaml || true
else
  echo "[refresh_homeassistant_runtime] no .devcontainer/configuration.yaml to copy"
fi

# Ensure custom_components symlink exists and points to repo's custom_components
if [ -e ".homeassistant/custom_components" ]; then
  echo "[refresh_homeassistant_runtime] .homeassistant/custom_components already exists"
else
  echo "[refresh_homeassistant_runtime] creating symlink .homeassistant/custom_components -> ../custom_components"
  ln -s ../custom_components .homeassistant/custom_components
fi

echo "[refresh_homeassistant_runtime] done"

