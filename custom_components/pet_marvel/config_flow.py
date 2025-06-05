import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_FRIENDLY_NAME,
    CONF_PASSWORD,
    CONF_EMAIL,
    CONF_COUNTRY,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorMode,
    SelectSelectorConfig,
)

from .api import PetMarvelAPI, APIAuthError, APIConnectionError
from .const import DOMAIN, VALID_COUNTRY_TO_CODE_MAPPING

_LOGGER = logging.getLogger(__name__)


class PetMarvelConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._country: None = None
        self._email: None = None
        self._password: None = None
        self._discovered_devices: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            self._country = user_input[CONF_COUNTRY]
            self._email = user_input[CONF_EMAIL]
            self._password = user_input[CONF_PASSWORD]
            try:
                session = async_get_clientsession(self.hass)
                api = PetMarvelAPI(session, self.hass.async_add_executor_job)
                await api.connect(self._country, self._email, self._password)

                devices = await api.get_devices()
                discovered_devices = {}

                for device in list(
                    filter(lambda dev: dev["categoryKey"] == "CatLitter", devices)
                ):
                    device_name = device["deviceName"]
                    device_id = device["iotId"]
                    discovered_devices[device_id] = device_name
                self._discovered_devices = discovered_devices
                return await self.async_step_device(None)
            except APIAuthError as e:
                _LOGGER.error(e)
                return self.async_abort(reason="authentication")
            except APIConnectionError as e:
                _LOGGER.error(e)
                return self.async_abort(reason="connection")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_COUNTRY): SelectSelector(
                        SelectSelectorConfig(
                            options=list(VALID_COUNTRY_TO_CODE_MAPPING.keys()),
                            mode=SelectSelectorMode.LIST,
                        )
                    ),
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
        )

    async def async_step_device(self, user_input) -> ConfigFlowResult:
        if user_input is not None:
            device_id = user_input[CONF_DEVICE_ID]
            await self.async_set_unique_id(device_id, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            data = {}
            data[CONF_DEVICE_ID] = device_id
            data[CONF_FRIENDLY_NAME] = self._discovered_devices[device_id]
            data[CONF_COUNTRY] = self._country
            data[CONF_EMAIL] = self._email
            data[CONF_PASSWORD] = self._password
            return self.async_create_entry(
                title=self._discovered_devices[device_id], data=data
            )

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="device",
            data_schema=vol.Schema(
                {vol.Required(CONF_DEVICE_ID): vol.In(self._discovered_devices)}
            ),
        )
