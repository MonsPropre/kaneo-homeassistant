"""Config flow for Kaneo integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import KaneoApiClient, KaneoAuthError, KaneoConnectionError
from .const import (
    CONF_API_TOKEN,
    CONF_BASE_URL,
    CONF_SCAN_INTERVAL,
    CONF_WORKSPACE_ID,
    DEFAULT_BASE_URL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def _validate_credentials(
    hass: HomeAssistant, base_url: str, api_token: str, workspace_id: str
) -> dict[str, str]:
    """Validate the user credentials and return errors dict."""
    errors: dict[str, str] = {}
    session = async_get_clientsession(hass)
    client = KaneoApiClient(base_url, api_token, workspace_id, session)

    try:
        valid = await client.validate_auth()
        if not valid:
            errors["base"] = "invalid_auth"
    except KaneoConnectionError:
        errors["base"] = "cannot_connect"
    except KaneoAuthError:
        errors["base"] = "invalid_auth"
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Unexpected error during Kaneo auth validation")
        errors["base"] = "unknown"

    return errors


class KaneoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kaneo."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            base_url = user_input[CONF_BASE_URL].rstrip("/")
            api_token = user_input[CONF_API_TOKEN]
            workspace_id = user_input[CONF_WORKSPACE_ID]

            # Avoid duplicates
            await self.async_set_unique_id(f"{base_url}_{workspace_id}")
            self._abort_if_unique_id_configured()

            errors = await _validate_credentials(
                self.hass, base_url, api_token, workspace_id
            )

            if not errors:
                return self.async_create_entry(
                    title=f"Kaneo ({workspace_id})",
                    data={
                        CONF_BASE_URL: base_url,
                        CONF_API_TOKEN: api_token,
                        CONF_WORKSPACE_ID: workspace_id,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
                vol.Required(CONF_API_TOKEN): str,
                vol.Required(CONF_WORKSPACE_ID): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> KaneoOptionsFlow:
        """Return the options flow."""
        return KaneoOptionsFlow(config_entry)


class KaneoOptionsFlow(config_entries.OptionsFlow):
    """Handle Kaneo options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )

        schema = vol.Schema(
            {
                vol.Required(CONF_SCAN_INTERVAL, default=current_interval): vol.All(
                    int, vol.Range(min=60, max=86400)
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
