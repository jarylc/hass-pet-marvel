import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import (
    UnitOfMass,
)
from datetime import datetime

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
    sensors: list[CoordinatorEntity] = [
        PetMarvelTimestampSensor(
            coordinator,
            device_info,
            translation="last_usage",
            key="last_usage",
            icon="mdi:toilet",
        ),
        PetMarvelMapSensor(
            coordinator,
            device_info,
            translation="status",
            key="work_status",
            options=[
                "idle",
                "cleaning",
                "cleaning_complete",
                "dumping",
                "dumping_complete",
                "resetting",
                "resetting_complete",
                "paused",
                "cat_approaching",
                "cat_entering",
            ],
            icon="mdi:state-machine",
        ),
        PetMarvelMapSensor(
            coordinator,
            device_info,
            translation="error_status",
            key="error_status",
            options=[
                "normal",
                "motor_failure",
                "magnet_clean_abnormal",
                "magnet_idle_abnormal",
                "weight_abnormal",
                "weight_high",
            ],
            icon="mdi:alert",
        ),
        PetMarvelSensor(
            coordinator,
            device_info,
            translation="software_version",
            key="software_version",
            icon="mdi:cellphone-arrow-down",
            visible=False,
        ),
    ]

    # for cat in coordinator.data.cat_list:
    #     sensors.append(
    #         PetMarvelCatSensor(
    #             coordinator,
    #             device_info,
    #             catName=cat["name"],
    #             catId=cat["id"],
    #             icon="mdi:cat",
    #         )
    #     )

    # Create the sensors.
    async_add_entities(sensors)


class PetMarvelCatSensor(CoordinatorEntity):
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PetMarvelCoordinator,
        deviceinfo: DeviceInfo,
        cat_name: str,
        cat_id: str,
        icon: str = None,
        visible: bool = True,
        category: str = None,
    ) -> None:
        super().__init__(coordinator)
        self.device_info = deviceinfo
        self.entity_registry_enabled_default = visible
        self._attr_translation_key = "cat_sensor"
        self._attr_translation_placeholders = {"name": cat_name}
        self._attr_unique_id = f"{coordinator.deviceid}-cat-{cat_id}"
        self._attr_unit_of_measurement = UnitOfMass.KILOGRAMS
        self._catId = cat_id
        if icon is not None:
            self._attr_icon = icon
        if category is not None:
            self._attr_entity_category = category

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()

    @property
    def _records(self):
        return list(
            filter(
                lambda record: record["cat_id"] == self._catId,
                self.coordinator.data.record_list,
            )
        )

    @property
    def state(self):
        if len(self._records) == 0:
            return 0
        last_record = self._records[0]
        return last_record["weight"]

    @property
    def extra_state_attributes(self):
        if len(self._records) == 0:
            return {}
        last_record = self._records[0]
        return {
            "state_class": SensorStateClass.MEASUREMENT,
            "start_time": datetime.fromtimestamp(last_record["start_time"]),
            "end_time": datetime.fromtimestamp(last_record["end_time"]),
        }


class PetMarvelSensor(CoordinatorEntity):
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PetMarvelCoordinator,
        deviceinfo: DeviceInfo,
        translation: str,
        key: str,
        unit: str = "",
        icon: str = None,
        visible: bool = True,
        category: str = None,
    ) -> None:
        super().__init__(coordinator)
        self.device_info = deviceinfo
        self.data_key = key
        self.translation_key = translation
        self.entity_registry_enabled_default = visible
        self._attr_unique_id = f"{coordinator.deviceid}-{translation}"
        self._attr_unit_of_measurement = unit
        if icon is not None:
            self._attr_icon = icon
        if category is not None:
            self._attr_entity_category = category

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()

    @property
    def state(self):
        return getattr(self.coordinator.data, self.data_key)

    @property
    def extra_state_attributes(self):
        return {"state_class": SensorStateClass.MEASUREMENT}


class PetMarvelMapSensor(CoordinatorEntity):
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PetMarvelCoordinator,
        deviceinfo: DeviceInfo,
        translation: str,
        key: str,
        options: list,
        icon: str = None,
        visible: bool = True,
    ) -> None:
        super().__init__(coordinator)
        self.device_info = deviceinfo
        self.data_key = key
        self.translation_key = translation
        self.entity_registry_enabled_default = visible
        self._attr_unique_id = f"{coordinator.deviceid}-{translation}"
        self.key_options = options
        if icon is not None:
            self._attr_icon = icon

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()

    @property
    def state(self):
        raw_value = getattr(self.coordinator.data, self.data_key)
        if raw_value >= len(self.key_options):
            return raw_value

        value = self.key_options[raw_value]
        if value is None:
            return raw_value

        return value


class PetMarvelTimestampSensor(CoordinatorEntity):
    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self,
        coordinator: PetMarvelCoordinator,
        deviceinfo: DeviceInfo,
        translation: str,
        key: str,
        icon: str = None,
        visible: bool = True,
    ) -> None:
        super().__init__(coordinator)
        self.device_info = deviceinfo
        self.data_key = key
        self.translation_key = translation
        self.entity_registry_enabled_default = visible
        self._attr_unique_id = f"{coordinator.deviceid}-{translation}"
        if icon is not None:
            self._attr_icon = icon

    @callback
    def _handle_coordinator_update(self) -> None:
        self.async_write_ha_state()

    @property
    def state(self):
        timestamp = getattr(self.coordinator.data, self.data_key) / 1000
        return datetime.fromtimestamp(timestamp)
