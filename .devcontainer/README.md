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
