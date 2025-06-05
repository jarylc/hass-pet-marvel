import logging

from homeassistant.config_entries import ConfigEntry
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
        PetMarvelButton(
            coordinator,
            device_info,
            translation="clean",
            service="clean",
            icon="mdi:broom",
        ),
        PetMarvelButton(
            coordinator,
            device_info,
            translation="level",
            service="level",
            icon="mdi:spirit-level",
        ),
        PetMarvelButton(
            coordinator,
            device_info,
            translation="dump",
            service="dump",
            icon="mdi:nuke",
            visible=False,
        ),
    ]

    # Create the sensors.
    async_add_entities(sensors)


class PetMarvelButton(CoordinatorEntity):
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PetMarvelCoordinator,
        deviceinfo: DeviceInfo,
        translation: str,
        service: str,
        icon: str = None,
        visible: bool = True,
    ) -> None:
        super().__init__(coordinator)
        self.device_info = deviceinfo
        self.service_key = service
        self.translation_key = translation
        self.entity_registry_enabled_default = visible
        self._attr_unique_id = f"{coordinator.deviceid}-{translation}"
        if icon is not None:
            self._attr_icon = icon

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()

    async def _async_press_action(self) -> None:
        await self.coordinator.invoke_service(self.service_key)
