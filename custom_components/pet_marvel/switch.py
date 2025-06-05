import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_ON,
    STATE_OFF,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import PetMarvelCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up the Sensors."""
    # This gets the data update coordinator from hass.data as specified in your __init__.py
    coordinator: PetMarvelCoordinator = hass.data[DOMAIN][
        config_entry.entry_id
    ].coordinator

    device_info = DeviceInfo(
        name=coordinator.device_name,
        manufacturer=MANUFACTURER,
        identifiers={(DOMAIN, coordinator.deviceid)},
    )

    # Enumerate all the sensors in your data value from your DataUpdateCoordinator and add an instance of your sensor class
    # to a list for each one.
    # This maybe different in your specific case, depending on how your data is structured
    sensors = [
        PetMarvelSwitch(
            coordinator,
            device_info,
            translation="auto_clean",
            key="AutoClean",
            icon="mdi:vacuum",
        ),
        PetMarvelSwitch(
            coordinator,
            device_info,
            translation="auto_bury",
            key="DeepClean",
            icon="mdi:shovel",
        ),
        PetMarvelSwitch(
            coordinator,
            device_info,
            translation="device_lights",
            key="LightSwitch",
            icon="mdi:spotlight",
        ),
        PetMarvelSwitch(
            coordinator,
            device_info,
            translation="small_cat_mode",
            key="SmallCatMode",
            icon="mdi:cat",
            visible=False,
        ),
    ]

    # Create the sensors.
    async_add_entities(sensors)


class PetMarvelSwitch(CoordinatorEntity):
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PetMarvelCoordinator,
        deviceinfo: DeviceInfo,
        translation: str,
        key: str,
        subkey: str = None,
        icon: str = None,
        visible: bool = True,
    ) -> None:
        super().__init__(coordinator)
        self.device_info = deviceinfo
        self.data_key = key
        self.data_subkey = subkey
        self.translation_key = translation
        self.entity_registry_enabled_default = visible
        self._attr_unique_id = f"{coordinator.deviceid}-{translation}"
        if icon is not None:
            self._attr_icon = icon

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()

    async def async_turn_on(self):
        await self._set_state(1)

    async def async_turn_off(self):
        await self._set_state(0)

    async def _set_state(self, state: int):
        """Helper to set device state."""
        if self.data_subkey is None:
            await self.coordinator.set_property(self.data_key, state)
            return

        value = getattr(self.coordinator.data, self.data_key, None)
        value[self.data_subkey] = state

        await self.coordinator.set_property(self.data_key, value)

    @property
    def is_on(self) -> bool:
        """Return the state of the sensor."""
        value = getattr(self.coordinator.data, self.data_key, None)

        if self.data_subkey is None:
            return value

        sub_value = value.get(self.data_subkey, None)

        return sub_value

    @property
    def state(self):
        return STATE_ON if self.is_on else STATE_OFF
