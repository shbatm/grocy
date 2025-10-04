# Grocy Custom Component for Home Assistant - AI Assistant Instructions

## Project Overview
This is a custom Home Assistant integration for Grocy, a self-hosted groceries & household management solution. The integration communicates with an existing Grocy installation to provide sensors and services in Home Assistant.

## Key Architecture Patterns

### Component Structure
- Main integration code lives in `custom_components/grocy/`
- Uses Home Assistant's data update coordinator pattern for efficient polling
- Follows Home Assistant's config flow pattern for UI-based configuration
- Integration is feature-flag aware - entities are dynamically enabled based on Grocy's enabled features

### Data Flow
1. `GrocyDataUpdateCoordinator` manages data updates using `pygrocy2` library
2. `GrocyData` class handles API interactions and data transformation
3. Entity components (`sensor.py`, `binary_sensor.py`) expose data as HA entities
4. Services (`services.py`) provide methods to interact with Grocy

## Development Workflows

### Setup
1. Install required Python packages: `pygrocy2==2.4.1`
2. Integration requires Grocy v3.2+ and Home Assistant 2021.12+
3. Configure a test Grocy instance (URL, API key, port) for development

### Testing
Add debug logging in `configuration.yaml`:
```yaml
logger:
  default: info
  logs:
   # Grocy Custom Component for Home Assistant — AI Assistant Instructions

   ## What this repo is
   This is a Home Assistant custom integration located at `custom_components/grocy/`.
   When the `grocy` folder is copied into a Home Assistant install under
   `/config/custom_components` and Home Assistant is restarted, the integration
   is loaded like a core integration and has access to Home Assistant's internal
   APIs, helpers and platform wiring (see `homeassistant/components/*`).

   It exposes sensors, binary sensors and services that mirror Grocy features
   (stock, shopping lists, tasks, chores, batteries, meal plans).

   ## High-level architecture (what to know quickly)
   - Entry point: `custom_components/grocy/__init__.py` — `async_setup_entry`:
      - Creates `GrocyDataUpdateCoordinator` and passes the `ConfigEntry`.
      - Stores coordinators per-config-entry in `hass.data[DOMAIN][entry_id]` to
        support multiple installs and avoid global state.
      - Calls `async_forward_entry_setups` with `PLATFORMS` from `const.py`.
      - Registers services (`services.py`) and image proxy endpoint (`grocy_data.py`).
   - Coordinator: `custom_components/grocy/coordinator.py` — `GrocyDataUpdateCoordinator`
      - Creates `pygrocy2.Grocy` client
      - Stores `grocy_data: GrocyData` and `entities: list[Entity]`
      - `_async_update_data()` iterates enabled entities and calls
         `GrocyData.async_update_data(key)` for each entity's `entity_description.key`
   - API layer: `custom_components/grocy/grocy_data.py` — wraps the `pygrocy2`
      client and transforms Grocy responses into the shapes entities expect
   - Entities: `sensor.py` and `binary_sensor.py` — define entity descriptions and
      read data from the coordinator's `data` payload
    - Services: `services.py` and `services.yaml` — service schemas and handlers.
       Services are registered once per integration load and should access the
       correct coordinator via `hass.data[DOMAIN][config_entry.entry_id]`.

   ## Important repo-specific conventions and gotchas
   - Entities are disabled by default. Tests and QA must explicitly enable
      entities in the Home Assistant UI to exercise them.
   - Available entities depend on Grocy feature flags. See
      `__init__._async_get_available_entities()` which calls
      `GrocyData.async_get_config()` and checks `grocy_config.enabled_features`.
   - `manifest.json` lists `pygrocy2==2.4.1` in `requirements` — when HA loads
      the integration it will attempt to ensure that dependency is available.
   - The integration uses Home Assistant's DataUpdateCoordinator pattern. Store
      coordinators per `ConfigEntry` in `hass.data[DOMAIN][entry_id]`. This
      allows multiple configured Grocy instances to coexist.

   ## Quick actionable examples (where to change things)
   - Adding a new sensor data key:
      1. Add a constant in `const.py` (e.g. `ATTR_MYFEATURE`).
      2. Implement data retrieval in `grocy_data.py` and expose via
          `GrocyData.async_update_data("myfeature")`.
      3. Add an entity with an `EntityDescription.key == "myfeature"` in
          `sensor.py` and include the platform in `PLATFORMS` if needed.
      4. Ensure the feature is added to `_async_get_available_entities()` if it's
          conditional on Grocy feature flags.
   - Adding/Changing a service:
      - Update `services.yaml` for the service schema and implement handler in
         `services.py`. Handlers should access the coordinator via
         `hass.data[DOMAIN][config_entry.entry_id]` and call into `grocy_data`.
      - Register services using `hass.services.async_register(DOMAIN, ...)` and
         validate inputs with voluptuous. Avoid mutating registries or
         entities from non-event-loop threads; use executor jobs and then
         notify the coordinator to refresh entities.

   ## Local development & debugging steps
   1. Copy `custom_components/grocy` into your Home Assistant `config/custom_components`.
   2. Restart Home Assistant.
   3. Configure the integration in the HA UI using Grocy URL, API key and port.
   4. Enable desired entities (all are disabled by default).

   Enable debug logs in `configuration.yaml` to trace behavior:
   ```yaml
   logger:
      default: info
      logs:
         pygrocy.grocy_api_client: debug
         custom_components.grocy: debug
   ```

   Notes: tests that exercise entities need them enabled in the UI or created by
   the test harness; the coordinator will skip disabled entities when updating.

   ## Key files to inspect when implementing features
   - `custom_components/grocy/__init__.py` — integration lifecycle & available entities
   - `custom_components/grocy/coordinator.py` — DataUpdateCoordinator wiring
   - `custom_components/grocy/grocy_data.py` — API wrapper + image proxy
   - `custom_components/grocy/sensor.py`, `binary_sensor.py` — entity definitions
   - `custom_components/grocy/services.py`, `services.yaml` — services & schemas
   - `custom_components/grocy/manifest.json` — HA metadata + dependency pin

   ## Dependencies and environments
   - The integration declares `pygrocy2==2.4.1` in `manifest.json`. Home Assistant
      will attempt to install this into its runtime environment when the
      integration is loaded. If developing locally in a venv, install the same
      version to match behavior:

   ```bash
   python -m pip install pygrocy2==2.4.1
   ```

   ## Try it (copyable commands)
   - Copy component into HA custom_components (example, adjust paths for your HA setup):

   ```bash
   cp -r custom_components/grocy /path/to/homeassistant/config/custom_components/
   # Restart Home Assistant service or container after copying
   ```

   - Enable debug logging by editing `configuration.yaml` (see snippet above) and
      then restarting Home Assistant.

   ## Grocy OpenAPI reference
   The Grocy REST API OpenAPI spec is a useful canonical source for field names
   and endpoints used by this integration. It documents models like
   `CurrentChoreResponse` (fields `chore_id`, `chore_name`) and the execute
   endpoint `POST /chores/{choreId}/execute` (payload: `tracked_time`,
   `done_by`, `skipped`). Use this URL when mapping entity attributes to API
   fields or when adding features that call Grocy endpoints:

   https://raw.githubusercontent.com/grocy/grocy/refs/heads/master/grocy.openapi.json

   Example: prefer `chore_id`/`chore_name` when extracting chore identifiers and
   labels instead of fragile heuristics.

   ## What an AI agent should do first (concise checklist)
   1. Read `__init__.py` and `coordinator.py` to understand startup & data flow.
   2. Inspect `grocy_data.py` to learn API methods and returned data shapes.
   3. Map entity `entity_description.key` values in `sensor.py`/`binary_sensor.py`
       to `GrocyData.async_update_data` keys.
   4. When changing runtime behavior, enable debug logs and test with a local
       Grocy instance configured in Home Assistant.

    If any section needs examples expanded (e.g., concrete snippets from a file),
    tell me which area to expand and I will add minimal code excerpts and tests.

## Adopted Home Assistant guidance (high-value items)

- Quality scale: this repo currently targets a pragmatic Bronze+/Silver level
   for a custom integration. See `quality_scale.yaml` guidance in the upstream
   instructions when raising the bar (diagnostics, strict typing, device
   management).
- Per-entry runtime data: store runtime/clients in `hass.data[DOMAIN][entry_id]`.
- Services: register services once and dispatch to per-entry handlers. Always
   validate inputs and run blocking API calls in `hass.async_add_executor_job`.
- Tests: add integration tests under `tests/components/grocy/` and mock external
   API responses. Use snapshots for entity states. Run `pre-commit` and ruff
   before submitting changes.

   ## Short examples & call sites
   - async_setup_entry (in `__init__.py`): creates the `GrocyDataUpdateCoordinator`,
      sets `hass.data[DOMAIN] = coordinator`, forwards platform setup with
      `hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)` and
      calls `async_setup_services()` and `async_setup_endpoint_for_image_proxy()`.
   - Data coordinator update (in `coordinator.py`): `_async_update_data()` loops
      over `coordinator.entities`, skips disabled entities, and calls
      `coordinator.grocy_data.async_update_data(entity.entity_description.key)`.
   - API mappings (in `grocy_data.py`): `GrocyData.entity_update_method` maps
      `ATTR_*` keys to methods like `async_update_stock`, `async_update_tasks`,
      `async_update_shopping_list`, etc. Add new data keys here to expose them.
   - Service wiring (in `services.py`): `async_setup_services()` registers a
      single handler `async_call_grocy_service()` that dispatches to specific
      functions (e.g., `async_add_product_service`, `async_execute_chore_service`)
      and uses `hass.services.async_register(DOMAIN, service, handler, schema)`.

   Small reproduction tip: to simulate an entity update locally, enable a
   relevant entity in Home Assistant, then call the service handler that modifies
   Grocy state (e.g., `grocy.add_product_to_stock`) and watch the coordinator
   logs as it refreshes that entity's data.