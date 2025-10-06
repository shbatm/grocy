"""Adds config flow for Grocy."""
from collections import OrderedDict
import logging
from typing import TYPE_CHECKING

from homeassistant import config_entries
from homeassistant.config_entries import OptionsFlowWithReload
from homeassistant.core import callback
import voluptuous as vol

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

from .const import (
    CONF_API_KEY,
    CONF_CREATE_CHORE_BUTTONS,
    CONF_PORT,
    CONF_URL,
    CONF_VERIFY_SSL,
    DEFAULT_PORT,
    DOMAIN,
    NAME,
)
from .helpers import extract_base_url_and_path

_LOGGER = logging.getLogger(__name__)


class GrocyFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Grocy."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Create the options flow for this config entry."""
        return GrocyOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}
        _LOGGER.debug("Step user")

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            valid = await self._test_credentials(
                user_input[CONF_URL],
                user_input[CONF_API_KEY],
                user_input.get(CONF_PORT, DEFAULT_PORT),
                user_input.get(CONF_VERIFY_SSL, False),
            )
            _LOGGER.debug("Testing of credentials returned: %s", valid)
            if valid:
                # Credentials validated — prompt the user for installation
                # options immediately (opt-in for chore buttons). Store the
                # validated config data temporarily and present the options
                # form as the next step in the same flow.
                self._validated_config = user_input
                options_schema = vol.Schema(
                    {vol.Optional(CONF_CREATE_CHORE_BUTTONS, default=False): bool}
                )
                return self.async_show_form(step_id="options", data_schema=options_schema)

            self._errors["base"] = "auth"
            return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)

    async def async_step_options(self, user_input=None):
        """Handle options submitted during the initial config flow."""
        # Ensure we have validated configuration stored from the previous step
        config_data = getattr(self, "_validated_config", None)
        if config_data is None:
            return self.async_abort(reason="unknown")

        if user_input is not None:
            # Create the config entry with the provided options
            return self.async_create_entry(title=NAME, data=config_data, options=user_input)

        # Show the options form if no input provided (shouldn't normally happen)
        options_schema = vol.Schema({vol.Optional(CONF_CREATE_CHORE_BUTTONS, default=False): bool})
        return self.async_show_form(step_id="options", data_schema=options_schema)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit the data."""
        data_schema = OrderedDict()
        data_schema[vol.Required(CONF_URL, default="")] = str
        data_schema[
            vol.Required(
                CONF_API_KEY,
                default="",
            )
        ] = str
        data_schema[vol.Optional(CONF_PORT, default=DEFAULT_PORT)] = int
        data_schema[vol.Optional(CONF_VERIFY_SSL, default=False)] = bool
        _LOGGER.debug("config form")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=self._errors,
        )

    async def _test_credentials(self, url, api_key, port, verify_ssl):
        """Return true if credentials is valid."""
        try:
            # Import pygrocy lazily so the config flow can still be loaded
            # (Home Assistant will install requirements when loading the
            # integration, but during local development the package may be
            # missing). Importing here avoids raising on module import which
            # would cause the config flow to be marked 'Not implemented'.
            try:
                from pygrocy2.grocy import Grocy
            except Exception:  # pragma: no cover - environment dependent
                _LOGGER.exception("pygrocy2 is not available during config flow")
                return False

            (base_url, path) = extract_base_url_and_path(url)
            client = Grocy(base_url, api_key, port=port, path=path, verify_ssl=verify_ssl)

            _LOGGER.debug("Testing credentials")

            def system_info():
                """Get system information from Grocy."""
                return client.get_system_info()

            await self.hass.async_add_executor_job(system_info)
            return True
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Error while testing credentials")
        return False


OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional("create_chore_buttons"): bool,
    }
)


class GrocyOptionsFlowHandler(OptionsFlowWithReload):
    def __init__(self, config_entry):
        """Options flow initialized with the target ConfigEntry."""
        self.config_entry = config_entry
        self._options = {}

    async def async_step_init(self, user_input=None):
        """Show and handle the options form for the config entry."""

        _LOGGER.debug(
            "Opening options flow for entry_id=%s current options=%s",
            getattr(self.config_entry, "entry_id", None),
            getattr(self.config_entry, "options", None),
        )

        if user_input is not None:
            # Let OptionsFlowWithReload handle persisting the options and
            # automatically reloading the config entry. Returning
            # async_create_entry is the documented pattern and avoids
            # manual calls to async_update_entry or async_reload.
            return self.async_create_entry(title="options", data=user_input)

        # Provide a short description so users understand the option's effect
        description = {
            "create_chore_buttons": (
                "When disabled, Grocy will not create dynamic chore 'Execute' button entities. "
                "Enable to expose per-chore execute buttons under the Grocy Chores device."
            )
        }

        # Use add_suggested_values_to_schema so the form is pre-filled with
        # existing saved option values from the config entry.
        data_schema = self.add_suggested_values_to_schema(OPTIONS_SCHEMA, self.config_entry.options)

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            description_placeholders=description,
        )

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}
        _LOGGER.debug("Step user")

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            valid = await self._test_credentials(
                user_input[CONF_URL],
                user_input[CONF_API_KEY],
                user_input[CONF_PORT],
                user_input[CONF_VERIFY_SSL],
            )
            _LOGGER.debug("Testing of credentials returned: ")
            _LOGGER.debug(valid)
            if valid:
                return self.async_create_entry(title=NAME, data=user_input)

            self._errors["base"] = "auth"
            return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit the data."""
        data_schema = OrderedDict()
        data_schema[vol.Required(CONF_URL, default="")] = str
        data_schema[
            vol.Required(
                CONF_API_KEY,
                default="",
            )
        ] = str
        data_schema[vol.Optional(CONF_PORT, default=DEFAULT_PORT)] = int
        data_schema[vol.Optional(CONF_VERIFY_SSL, default=False)] = bool
        _LOGGER.debug("config form")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=self._errors,
        )

    async def _test_credentials(self, url, api_key, port, verify_ssl):
        """Return true if credentials is valid."""
        try:
            # Import pygrocy lazily so the config flow can still be loaded
            # (Home Assistant will install requirements when loading the
            # integration, but during local development the package may be
            # missing). Importing here avoids raising on module import which
            # would cause the config flow to be marked 'Not implemented'.
            try:
                from pygrocy2.grocy import Grocy
            except Exception:  # pragma: no cover - environment dependent
                _LOGGER.exception("pygrocy2 is not available during options flow")
                return False

            (base_url, path) = extract_base_url_and_path(url)
            client = Grocy(base_url, api_key, port=port, path=path, verify_ssl=verify_ssl)

            _LOGGER.debug("Testing credentials")

            def system_info():
                """Get system information from Grocy."""
                return client.get_system_info()

            await self.hass.async_add_executor_job(system_info)
            return True
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Error while testing credentials")
        return False
