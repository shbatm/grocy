Devcontainer: running tests for this custom component

This devcontainer is configured to let maintainers run the integration's tests against Home Assistant's pytest fixtures.

Quick steps after opening the repository in the Dev Container:

1. The container build will run the setup script automatically (via `postCreateCommand`).
   - The script creates a virtualenv at `/workspaces/grocy/.venv` and installs a pre-release of `homeassistant` from PyPI (including testing extras when available).

2. Open a terminal in the container and activate the venv:

```bash
cd /workspaces/grocy
source .venv/bin/activate
```

3. Run the tests for this integration:

```bash
pytest tests/components/grocy -q
```

Notes and troubleshooting
- If the container build fails due to missing system dependencies while building wheels (cryptography, etc.), rebuild the container after adding the required package to `.devcontainer/Dockerfile` (for example `libssl-dev` and `cargo` are already included).
- To pin a specific Home Assistant version, edit `.devcontainer/scripts/setup_ha_test_env.sh` and replace the `pip install --pre "homeassistant[tests]"` line with a pinned version, for example:

```bash
python -m pip install --pre 'homeassistant==2025.10.0rc1[tests]'
```

If you'd like, I can update the README to include a suggested pinned HA version or CI snippets to run these tests in GitHub Actions.


VS Code Tasks
--------------

The workspace includes two VS Code tasks in `.vscode/tasks.json`:

- "Start Home Assistant (devcontainer)": runs Home Assistant using the venv at `/opt/venv` when available, or falls back to `python3 -m homeassistant`.
   - It runs Home Assistant with the workspace mounted as the config directory so your `configuration.yaml` and `custom_components/` are read from the repo.
   - The task starts HA bound to port 9123 (inside the container) so you can map it out via the devcontainer ports.
   - It runs Home Assistant using the `.homeassistant` directory in the workspace as the config directory. The setup script copies the default `configuration.yaml` into `.homeassistant/` and creates a symlink `.homeassistant/custom_components` → `../custom_components` so HA reads your development `custom_components` but runtime files are kept in `.homeassistant/` instead of cluttering the repo root.

- "Stop Home Assistant (kill)": convenience task that stops any running Home Assistant process in the container.

- "Start Home Assistant (with venv activate)": convenience task that sources `/opt/venv/bin/activate` (if present) before launching Home Assistant. Use this when you want the venv explicitly activated in the terminal task.

Usage (inside the devcontainer):

1. Open the Command Palette (Ctrl+Shift+P) and run "Tasks: Run Task" → one of the Start tasks.
2. The Home Assistant process will run in the Terminal panel in the foreground (the terminal will show HA logs and remain interactive).
3. To stop it, press Ctrl+C in the task terminal or run the "Stop Home Assistant (kill)" task.

Tip: If you want your terminal session to have the venv activated for other commands, run the "Start Home Assistant (with venv activate)" task — it will activate the venv in the task's shell before launching HA.

Notes:
   - The Start task is configured to use the workspace root (`/workspaces/grocy`) as the Home Assistant configuration directory (passed as `--config /workspaces/grocy`). This makes it easy to edit `configuration.yaml` and `custom_components/` in the repo and have Home Assistant pick up the changes when restarted. If you prefer a different mount, edit `.vscode/tasks.json`.
   Note: a sample `configuration.yaml` is included in the devcontainer at `.devcontainer/configuration.yaml`.
   The setup script (`.devcontainer/scripts/setup_homeassistant_runtime.sh`) will copy this file into the runtime folder as `.homeassistant/configuration.yaml` when the container is created.
- The devcontainer already maps container port 8123 to host port 9123 in `.devcontainer/devcontainer.json` so you can reach Home Assistant at localhost:9123 on the host machine.
 - The `.homeassistant/` directory is added to `.gitignore` so runtime state/config doesn't get committed.
