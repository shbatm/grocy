#!/usr/bin/env bash
# Idempotent refresh helper for .homeassistant runtime folder.
# Use when you want to re-copy the default configuration or re-create the symlink.
set -euo pipefail
# Calculate the repository root (two levels up from this scripts directory),
# matching setup_homeassistant_runtime.sh so we operate on the repo root.
repo_root="$(cd "$(dirname "$0")/../.." && pwd -P)"
cd "$repo_root"

echo "[refresh_homeassistant_runtime] repo_root=$repo_root"

if [ -d "$repo_root/.homeassistant" ]; then
  echo "[refresh_homeassistant_runtime] $repo_root/.homeassistant exists"
else
  echo "[refresh_homeassistant_runtime] $repo_root/.homeassistant missing, creating"
  mkdir -p "$repo_root/.homeassistant"
fi

# Copy configuration.yaml only if upstream devcontainer copy exists
if [ -f "$repo_root/.devcontainer/configuration.yaml" ]; then
  echo "[refresh_homeassistant_runtime] copying $repo_root/.devcontainer/configuration.yaml -> $repo_root/.homeassistant/configuration.yaml"
  cp -n "$repo_root/.devcontainer/configuration.yaml" "$repo_root/.homeassistant/configuration.yaml" || true
else
  echo "[refresh_homeassistant_runtime] no $repo_root/.devcontainer/configuration.yaml to copy"
fi

# Ensure custom_components symlink exists and points to repo's custom_components
if [ -e "$repo_root/.homeassistant/custom_components" ]; then
  echo "[refresh_homeassistant_runtime] $repo_root/.homeassistant/custom_components already exists"
else
  echo "[refresh_homeassistant_runtime] creating symlink $repo_root/.homeassistant/custom_components -> ../custom_components"
  ln -s ../custom_components "$repo_root/.homeassistant/custom_components"
fi

echo "[refresh_homeassistant_runtime] done"

