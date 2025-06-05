import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_FRIENDLY_NAME,
    CONF_PASSWORD,
    CONF_COUNTRY,
    CONF_EMAIL,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PetMarvelAPI, APIAuthError, APIConnectionError
from .const import DOMAIN
from .value_cacher import ValueCacher

_LOGGER = logging.getLogger(__name__)

_SERVICE_MAPPING = {
    "clean": 0,
    "level": 1,
    "dump": 2,
}


@dataclass
class PetMarvelAPIData:
    """Class to hold api data."""

    work_status: int
    up_lid_status: bool
    drawer_status: bool
    full_status: bool
    last_usage: int
    error_status: int

    AutoClean: bool
    DeepClean: bool
    SmallCatMode: bool
    LightSwitch: bool

    software_version: str
    # cat_list: list[object] = field(default_factory=list)
    # record_list: list[object] = field(default_factory=list)


class PetMarvelCoordinator(DataUpdateCoordinator):
    """My coordinator."""

    data: PetMarvelAPIData

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""

        # Set variables from values entered in config flow setup
        self.deviceid = config_entry.data[CONF_DEVICE_ID]
        self.device_name = config_entry.data[CONF_FRIENDLY_NAME]
        self.country = config_entry.data[CONF_COUNTRY]
        self.email = config_entry.data[CONF_EMAIL]
        self.password = config_entry.data[CONF_PASSWORD]

        self._device_name = None
        self.last_usage = None

        self._recordsCache = ValueCacher(
            refresh_after=timedelta(minutes=30), discard_after=timedelta(hours=4)
        )
        self._devicePropertiesCache = ValueCacher(
            refresh_after=timedelta(seconds=0), discard_after=timedelta(minutes=30)
        )

        # Initialise DataUpdateCoordinator
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} ({config_entry.unique_id})",
            # Method to call on every update interval.
            update_method=self.async_update_data,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=30),
        )

        # Initialise api here
        session = async_get_clientsession(hass)
        self.api = PetMarvelAPI(session, hass.async_add_executor_job)

    async def set_property(self, key: str, value: Any):
        await self.api.connect(self.country, self.email, self.password)
        await self.api.set_device_properties(self.deviceid, {key: value})
        # update data
        setattr(self.data, key, value)
        self.async_set_updated_data(self.data)

    async def invoke_service(self, service: str):
        await self.api.connect(self.country, self.email, self.password)
        if service not in _SERVICE_MAPPING:
            raise Exception("cannot find service to invoke")
        await self.set_property("DeviceControl", _SERVICE_MAPPING[service])

    async def _get_device_name(self):
        if self._device_name is not None:
            return self._device_name

        """get deviceName by iotId"""
        await self.api.connect(self.country, self.email, self.password)
        devices = await self.api.get_devices()
        devices = list(filter(lambda dev: dev["iotId"] == self.deviceid, devices))
        if len(devices) == 0:
            raise APIConnectionError("iotId not found in device list")
        device_name = devices[0]["deviceName"]
        self._device_name = device_name
        return device_name

    # async def _get_records(self):
    #     async def fetch():
    #         await self.api.connect(self.country, self.username, self.password)
    #         deviceName = await self._getDeviceName()
    #         return await self.api.getRecords(deviceName)
    #
    #     return await self._recordsCache.get_or_update(fetch)

    async def _get_device_properties(self):
        async def fetch():
            await self.api.connect(self.country, self.email, self.password)
            return await self.api.get_device_properties(self.deviceid)

        return await self._devicePropertiesCache.get_or_update(fetch)

    async def async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            devicedata = await self._get_device_properties()

            last_usage = devicedata["ExcreteTimes"]["time"]

            if self.last_usage != last_usage:
                self._recordsCache.mark_as_stale()

            self.last_usage = last_usage

            # records = await self._getRecords()

            try:
                return PetMarvelAPIData(
                    work_status=devicedata["workstatus"]["value"],
                    up_lid_status=devicedata["UpLidStatus"]["value"] == 0,
                    drawer_status=devicedata["DrawerSatus"]["value"] == 0,
                    full_status=devicedata["FullStatus"]["value"] == 1,
                    last_usage=last_usage,
                    error_status=devicedata["ErrStatus"]["value"],
                    AutoClean=devicedata["AutoClean"]["value"] == 1,
                    DeepClean=devicedata["DeepClean"]["value"] == 1,
                    SmallCatMode=devicedata["SmallCatMode"]["value"] == 1,
                    LightSwitch=devicedata["LightSwitch"]["value"] == 1,
                    software_version=devicedata["SoftwareVersion"]["value"],
                )
            except Exception as err:
                _LOGGER.error(err)
                # This will show entities as unavailable by raising UpdateFailed exception
                raise UpdateFailed(
                    "Got no data from API, please try to restart your litter box."
                ) from err
        except APIAuthError as err:
            _LOGGER.error(err)
            raise UpdateFailed(err) from err
        except APIConnectionError as err:
            _LOGGER.error(err)
            raise UpdateFailed(err) from err
