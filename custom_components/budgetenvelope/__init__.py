"""The envelope-budget integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_FILE_PATH
from homeassistant.core import HomeAssistant, callback

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

import logging
import json
from datetime import timedelta
import math
import async_timeout

_LOGGER = logging.getLogger(__name__)

from .const import DOMAIN

# For your initial PR, limit it to 1 platform.
PLATFORMS: list[Platform] = [Platform.SENSOR]  # PLATFORM.TEXT


def get_object_value(value) -> str:
    """Get value from object or enum."""

    while hasattr(value, "value"):
        value = value.value

    return value


# async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> bool:
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up envelope-budget from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    # Fetch initial data so we have data when entities subscribe
    #
    # If the refresh fails, async_config_entry_first_refresh will
    # raise ConfigEntryNotReady and setup will try again later
    #
    # If you do not want to retry setup on failure, use
    # coordinator.async_refresh() instead
    #

    coordinator = EnvelopeCoordinator(hass, "dummyfile")

    hass.data[DOMAIN][entry.entry_id + "_coordinator"] = coordinator

    await coordinator.async_config_entry_first_refresh()

    # my_api = hass.data[DOMAIN][entry.entry_id]
    # coordinator = EnvelopeCoordinator(hass, my_api)

    # async_add_entities(
    #    BudgetEnvelope(coordinator, idx) for idx, ent in enumerate(coordinator.data)
    # )

    # Setup components
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id + "_coordinator")

    return unload_ok


class EnvelopeCoordinator(DataUpdateCoordinator):
    """envelope coordinator."""

    def __init__(self, hass, state_file):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Budget Envelopes Coordinator?!",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=180),
        )
        self.state_file = state_file
        self.state_last_read = "now"
        self.raw_states = None
        self.data = {}

    def read_states(self):
        "Reads the states from a file and preprocesses them."

        with open(
            self.config_entry.data[CONF_FILE_PATH], encoding="utf8"
        ) as statesfile:
            self.raw_states = json.loads("\n".join(statesfile.readlines()))
        # self.raw_states = FILECONTENTS

    def process_states(self):
        "kk."
        if self.raw_states is None:
            return

        for env in self.raw_states:
            if (
                "carryover" not in env
                or env["carryover"] is None
                or math.isnan(env["carryover"])
            ):
                env["carryover"] = 0

            if env["state"] > 0:
                env["state_percentage"] = round(
                    env["state"] / (env["budget"] + env["carryover"]) * 100, 2
                )
            else:
                env["state_percentage"] = 0.0

            env["state"] = round(env["state"], 2)
            env["carryover"] = round(env["carryover"], 2)
            env["budget"] = round(env["budget"], 2)

            if env["envelope"] == "":
                env["envelope"] = "All"

            self.data[env["envelope"]] = env

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                self.read_states()
                self.process_states()
                # Grab active context variables to limit data required to be fetched from API
                # Note: using context is not required if there is no need or ability to limit
                # data retrieved from API.
                # listening_idx = set(self.async_contexts())

                return self.data
        except Exception as e:
            print(e)
            raise Exception()
        # except ApiAuthError as err:
        # Raising ConfigEntryAuthFailed will cancel future updates
        # and start a config flow with SOURCE_REAUTH (async_step_reauth)
        #    raise ConfigEntryAuthFailed from err
        # except ApiError as err:
        #    raise UpdateFailed(f"Error communicating with API: {err}")


class BudgetEnvelopeBaseEntity(CoordinatorEntity):
    """Common base for VolkswagenID entities."""

    # _attr_should_poll = False
    _attr_attribution = (
        "Data read from the .json with specified format and storage location by"
    )

    def __init__(self, coordinator, idx):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator, context=idx)
        self.index = idx

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{self.data['envelope']}")},
            name=f"{self.data['envelope']} Envelope",
        )

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return self._attr_device_info

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        # self._attr_is_on = self.coordinator.data[self.idx]["state"]
        self.async_write_ha_state()

    @property
    def data(self):
        """Shortcut to access coordinator data for the entity."""
        return self.coordinator.data[self.index]


FILECONTENTS = [
    {
        "envelope": "",
        "month": "2023-11",
        "budget": 10458.0,
        "state_month": 729.0,
        "state": -9685.0,
        "carryover": -10413.92,
    },
    {
        "envelope": "",
        "month": "2023-12",
        "budget": 116.0,
        "state_month": -10604.0,
        "state": -20289.0,
        "carryover": -9685.17,
    },
    {
        "envelope": "",
        "month": "2024-01",
        "budget": 10521.0,
        "state_month": 5287.0,
        "state": -15002.0,
        "carryover": -20289.04,
    },
    {
        "envelope": "Auto",
        "month": "2023-10",
        "budget": 541.0,
        "state_month": 66.0,
        "state": 66.0,
        "carryover": None,
    },
    {
        "envelope": "Auto",
        "month": "2023-11",
        "budget": 541.0,
        "state_month": -75.0,
        "state": -9.0,
        "carryover": 65.67000000000002,
    },
    {
        "envelope": "Auto",
        "month": "2023-12",
        "budget": 541.0,
        "state_month": -36.0,
        "state": -45.0,
        "carryover": -9.180000000000007,
    },
    {
        "envelope": "Auto",
        "month": "2024-01",
        "budget": 541.0,
        "state_month": 191.0,
        "state": 146.0,
        "carryover": -45.23999999999995,
    },
    {
        "envelope": "Auto:Darlehen",
        "month": "2023-10",
        "budget": 350.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": None,
    },
    {
        "envelope": "Auto:Darlehen",
        "month": "2023-11",
        "budget": 350.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": 0.0,
    },
    {
        "envelope": "Auto:Darlehen",
        "month": "2023-12",
        "budget": 350.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": 0.0,
    },
    {
        "envelope": "Auto:Darlehen",
        "month": "2024-01",
        "budget": 350.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": 0.0,
    },
    {
        "envelope": "Auto:Laden",
        "month": "2023-10",
        "budget": 40.0,
        "state_month": 35.0,
        "state": 35.0,
        "carryover": None,
    },
    {
        "envelope": "Auto:Laden",
        "month": "2023-11",
        "budget": 40.0,
        "state_month": -83.0,
        "state": -48.0,
        "carryover": 34.57,
    },
    {
        "envelope": "Auto:Laden",
        "month": "2023-12",
        "budget": 40.0,
        "state_month": -5.0,
        "state": -54.0,
        "carryover": -48.279999999999994,
    },
    {
        "envelope": "Auto:Laden",
        "month": "2024-01",
        "budget": 40.0,
        "state_month": 40.0,
        "state": -14.0,
        "carryover": -53.50999999999999,
    },
    {
        "envelope": "Auto:Parking",
        "month": "2023-10",
        "budget": 15.0,
        "state_month": -22.0,
        "state": -22.0,
        "carryover": None,
    },
    {
        "envelope": "Auto:Parking",
        "month": "2023-11",
        "budget": 15.0,
        "state_month": 13.0,
        "state": -9.0,
        "carryover": -21.9,
    },
    {
        "envelope": "Auto:Parking",
        "month": "2023-12",
        "budget": 15.0,
        "state_month": -26.0,
        "state": -35.0,
        "carryover": -8.899999999999999,
    },
    {
        "envelope": "Auto:Parking",
        "month": "2024-01",
        "budget": 15.0,
        "state_month": 15.0,
        "state": -20.0,
        "carryover": -34.73,
    },
    {
        "envelope": "Bildung",
        "month": "2023-11",
        "budget": 90.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": 0.0,
    },
    {
        "envelope": "Bildung",
        "month": "2023-12",
        "budget": 90.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": 0.0,
    },
    {
        "envelope": "Bildung",
        "month": "2024-01",
        "budget": 90.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": 0.0,
    },
    {
        "envelope": "Bildung:Kinder",
        "month": "2023-11",
        "budget": 90.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": 0.0,
    },
    {
        "envelope": "Bildung:Kinder",
        "month": "2023-12",
        "budget": 90.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": 0.0,
    },
    {
        "envelope": "Bildung:Kinder",
        "month": "2024-01",
        "budget": 90.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": 0.0,
    },
    {
        "envelope": "B\u00fcrokratie",
        "month": "2023-10",
        "budget": 1263.0,
        "state_month": 21.0,
        "state": 21.0,
        "carryover": None,
    },
    {
        "envelope": "B\u00fcrokratie",
        "month": "2023-11",
        "budget": 1263.0,
        "state_month": 21.0,
        "state": 42.0,
        "carryover": 21.190000000000055,
    },
    {
        "envelope": "B\u00fcrokratie",
        "month": "2023-12",
        "budget": 1263.0,
        "state_month": -50.0,
        "state": -8.0,
        "carryover": 42.38000000000011,
    },
    {
        "envelope": "B\u00fcrokratie",
        "month": "2024-01",
        "budget": 1263.0,
        "state_month": 32.0,
        "state": 24.0,
        "carryover": -7.6099999999999,
    },
    {
        "envelope": "B\u00fcrokratie:Banken",
        "month": "2023-10",
        "budget": 21.0,
        "state_month": 21.0,
        "state": 21.0,
        "carryover": None,
    },
    {
        "envelope": "B\u00fcrokratie:Banken",
        "month": "2023-11",
        "budget": 21.0,
        "state_month": 21.0,
        "state": 42.0,
        "carryover": 21.0,
    },
    {
        "envelope": "B\u00fcrokratie:Banken",
        "month": "2023-12",
        "budget": 21.0,
        "state_month": -50.0,
        "state": -8.0,
        "carryover": 42.0,
    },
    {
        "envelope": "B\u00fcrokratie:Banken",
        "month": "2024-01",
        "budget": 21.0,
        "state_month": 21.0,
        "state": 13.0,
        "carryover": -8.179999999999993,
    },
    {
        "envelope": "B\u00fcrokratie:Steuer",
        "month": "2023-10",
        "budget": 1150.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": None,
    },
    {
        "envelope": "B\u00fcrokratie:Steuer",
        "month": "2023-11",
        "budget": 1150.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": 0.0,
    },
    {
        "envelope": "B\u00fcrokratie:Steuer",
        "month": "2023-12",
        "budget": 1150.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": 0.0,
    },
    {
        "envelope": "B\u00fcrokratie:Steuer",
        "month": "2024-01",
        "budget": 1150.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": 0.0,
    },
    {
        "envelope": "B\u00fcrokratie:Versicherungen",
        "month": "2023-10",
        "budget": 92.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": None,
    },
    {
        "envelope": "B\u00fcrokratie:Versicherungen",
        "month": "2023-11",
        "budget": 92.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": 0.18999999999999773,
    },
    {
        "envelope": "B\u00fcrokratie:Versicherungen",
        "month": "2023-12",
        "budget": 92.0,
        "state_month": 0.0,
        "state": 1.0,
        "carryover": 0.37999999999999545,
    },
    {
        "envelope": "B\u00fcrokratie:Versicherungen",
        "month": "2024-01",
        "budget": 92.0,
        "state_month": 11.0,
        "state": 12.0,
        "carryover": 0.5699999999999932,
    },
    {
        "envelope": "Freizeit",
        "month": "2023-10",
        "budget": 265.0,
        "state_month": 73.0,
        "state": 73.0,
        "carryover": None,
    },
    {
        "envelope": "Freizeit",
        "month": "2023-11",
        "budget": 265.0,
        "state_month": -30.0,
        "state": 43.0,
        "carryover": 73.35000000000002,
    },
    {
        "envelope": "Freizeit",
        "month": "2023-12",
        "budget": 96.0,
        "state_month": -96.0,
        "state": -53.0,
        "carryover": 43.0,
    },
    {
        "envelope": "Freizeit",
        "month": "2024-01",
        "budget": 265.0,
        "state_month": -103.0,
        "state": -156.0,
        "carryover": -53.39999999999998,
    },
    {
        "envelope": "Freizeit:Ausgehen",
        "month": "2023-10",
        "budget": 150.0,
        "state_month": 31.0,
        "state": 31.0,
        "carryover": None,
    },
    {
        "envelope": "Freizeit:Ausgehen",
        "month": "2023-11",
        "budget": 150.0,
        "state_month": -12.0,
        "state": 18.0,
        "carryover": 30.700000000000003,
    },
    {
        "envelope": "Freizeit:Ausgehen",
        "month": "2023-12",
        "budget": 71.0,
        "state_month": -18.0,
        "state": -0.0,
        "carryover": 18.200000000000003,
    },
    {
        "envelope": "Freizeit:Ausgehen",
        "month": "2024-01",
        "budget": 150.0,
        "state_month": 150.0,
        "state": 150.0,
        "carryover": -0.269999999999996,
    },
    {
        "envelope": "Freizeit:Kinder",
        "month": "2023-10",
        "budget": 40.0,
        "state_month": 26.0,
        "state": 26.0,
        "carryover": None,
    },
    {
        "envelope": "Freizeit:Kinder",
        "month": "2023-11",
        "budget": 40.0,
        "state_month": -42.0,
        "state": -16.0,
        "carryover": 25.5,
    },
    {
        "envelope": "Freizeit:Kinder",
        "month": "2023-12",
        "budget": 40.0,
        "state_month": 20.0,
        "state": 4.0,
        "carryover": -16.400000000000006,
    },
    {
        "envelope": "Freizeit:Kinder",
        "month": "2024-01",
        "budget": 40.0,
        "state_month": 40.0,
        "state": 44.0,
        "carryover": 3.7999999999999936,
    },
    {
        "envelope": "Freizeit:Kultur",
        "month": "2023-10",
        "budget": 40.0,
        "state_month": 40.0,
        "state": 40.0,
        "carryover": None,
    },
    {
        "envelope": "Freizeit:Kultur",
        "month": "2023-11",
        "budget": 40.0,
        "state_month": 40.0,
        "state": 80.0,
        "carryover": 40.0,
    },
    {
        "envelope": "Freizeit:Kultur",
        "month": "2024-01",
        "budget": 40.0,
        "state_month": 40.0,
        "state": 40.0,
        "carryover": 0.0,
    },
    {
        "envelope": "Freizeit:Medien",
        "month": "2023-10",
        "budget": 35.0,
        "state_month": -13.0,
        "state": -13.0,
        "carryover": None,
    },
    {
        "envelope": "Freizeit:Medien",
        "month": "2023-11",
        "budget": 35.0,
        "state_month": 16.0,
        "state": 3.0,
        "carryover": -12.849999999999994,
    },
    {
        "envelope": "Freizeit:Medien",
        "month": "2023-12",
        "budget": 35.0,
        "state_month": 16.0,
        "state": 19.0,
        "carryover": 3.2000000000000064,
    },
    {
        "envelope": "Freizeit:Medien",
        "month": "2024-01",
        "budget": 35.0,
        "state_month": 35.0,
        "state": 54.0,
        "carryover": 19.250000000000007,
    },
    {
        "envelope": "Gesundheit",
        "month": "2023-10",
        "budget": 1160.0,
        "state_month": -127.0,
        "state": -127.0,
        "carryover": None,
    },
    {
        "envelope": "Gesundheit",
        "month": "2023-11",
        "budget": 660.0,
        "state_month": 116.0,
        "state": -11.0,
        "carryover": -126.84999999999991,
    },
    {
        "envelope": "Gesundheit",
        "month": "2023-12",
        "budget": 944.0,
        "state_month": -36.0,
        "state": -46.0,
        "carryover": -10.589999999999918,
    },
    {
        "envelope": "Gesundheit",
        "month": "2024-01",
        "budget": 1223.0,
        "state_month": 1223.0,
        "state": 1177.0,
        "carryover": -46.08999999999992,
    },
    {
        "envelope": "Gesundheit:Arzt",
        "month": "2023-10",
        "budget": 100.0,
        "state_month": -180.0,
        "state": -180.0,
        "carryover": None,
    },
    {
        "envelope": "Gesundheit:Arzt",
        "month": "2023-11",
        "budget": 332.0,
        "state_month": 116.0,
        "state": -64.0,
        "carryover": -180.14999999999998,
    },
    {
        "envelope": "Gesundheit:Arzt",
        "month": "2023-12",
        "budget": 403.0,
        "state_month": 64.0,
        "state": -0.0,
        "carryover": -63.889999999999986,
    },
    {
        "envelope": "Gesundheit:Arzt",
        "month": "2024-01",
        "budget": 100.0,
        "state_month": 100.0,
        "state": 100.0,
        "carryover": -0.2899999999999636,
    },
    {
        "envelope": "Gesundheit:Krankenversicherung",
        "month": "2023-10",
        "budget": 1060.0,
        "state_month": 65.0,
        "state": 65.0,
        "carryover": None,
    },
    {
        "envelope": "Gesundheit:Krankenversicherung",
        "month": "2023-11",
        "budget": 328.0,
        "state_month": 0.0,
        "state": 65.0,
        "carryover": 65.39999999999998,
    },
    {
        "envelope": "Gesundheit:Krankenversicherung",
        "month": "2023-12",
        "budget": 541.0,
        "state_month": -55.0,
        "state": 10.0,
        "carryover": 65.39999999999998,
    },
    {
        "envelope": "Gesundheit:Krankenversicherung",
        "month": "2024-01",
        "budget": 1123.0,
        "state_month": 1123.0,
        "state": 1133.0,
        "carryover": 10.399999999999977,
    },
    {
        "envelope": "Haushalt",
        "month": "2023-10",
        "budget": 1820.0,
        "state_month": -270.0,
        "state": -270.0,
        "carryover": None,
    },
    {
        "envelope": "Haushalt",
        "month": "2023-11",
        "budget": 1820.0,
        "state_month": 109.0,
        "state": -161.0,
        "carryover": -269.6399999999999,
    },
    {
        "envelope": "Haushalt",
        "month": "2023-12",
        "budget": 2026.0,
        "state_month": 87.0,
        "state": -74.0,
        "carryover": -160.56999999999994,
    },
    {
        "envelope": "Haushalt",
        "month": "2024-01",
        "budget": 1820.0,
        "state_month": 1820.0,
        "state": 1746.0,
        "carryover": -73.95000000000005,
    },
    {
        "envelope": "Haushalt:Bekleidung",
        "month": "2023-10",
        "budget": 100.0,
        "state_month": 96.0,
        "state": 96.0,
        "carryover": None,
    },
    {
        "envelope": "Haushalt:Bekleidung",
        "month": "2023-11",
        "budget": 100.0,
        "state_month": -50.0,
        "state": 46.0,
        "carryover": 96.03999999999999,
    },
    {
        "envelope": "Haushalt:Bekleidung",
        "month": "2023-12",
        "budget": 100.0,
        "state_month": -70.0,
        "state": -24.0,
        "carryover": 45.66,
    },
    {
        "envelope": "Haushalt:Bekleidung",
        "month": "2024-01",
        "budget": 100.0,
        "state_month": 100.0,
        "state": 76.0,
        "carryover": -24.140000000000015,
    },
    {
        "envelope": "Haushalt:En Gros",
        "month": "2023-10",
        "budget": 30.0,
        "state_month": -117.0,
        "state": -117.0,
        "carryover": None,
    },
    {
        "envelope": "Haushalt:En Gros",
        "month": "2023-11",
        "budget": 30.0,
        "state_month": 30.0,
        "state": -87.0,
        "carryover": -117.30000000000001,
    },
    {
        "envelope": "Haushalt:En Gros",
        "month": "2023-12",
        "budget": 30.0,
        "state_month": 30.0,
        "state": -57.0,
        "carryover": -87.30000000000001,
    },
    {
        "envelope": "Haushalt:En Gros",
        "month": "2024-01",
        "budget": 30.0,
        "state_month": 30.0,
        "state": -27.0,
        "carryover": -57.30000000000001,
    },
    {
        "envelope": "Haushalt:Kinder",
        "month": "2023-10",
        "budget": 170.0,
        "state_month": -40.0,
        "state": -40.0,
        "carryover": None,
    },
    {
        "envelope": "Haushalt:Kinder",
        "month": "2023-11",
        "budget": 170.0,
        "state_month": 86.0,
        "state": 46.0,
        "carryover": -39.53,
    },
    {
        "envelope": "Haushalt:Kinder",
        "month": "2023-12",
        "budget": 286.0,
        "state_month": -77.0,
        "state": -31.0,
        "carryover": 46.42,
    },
    {
        "envelope": "Haushalt:Kinder",
        "month": "2024-01",
        "budget": 170.0,
        "state_month": 170.0,
        "state": 139.0,
        "carryover": -30.91000000000004,
    },
    {
        "envelope": "Haushalt:Lebensmittel",
        "month": "2023-10",
        "budget": 1250.0,
        "state_month": -216.0,
        "state": -216.0,
        "carryover": None,
    },
    {
        "envelope": "Haushalt:Lebensmittel",
        "month": "2023-11",
        "budget": 1250.0,
        "state_month": -8.0,
        "state": -225.0,
        "carryover": -216.3499999999999,
    },
    {
        "envelope": "Haushalt:Lebensmittel",
        "month": "2023-12",
        "budget": 1250.0,
        "state_month": 181.0,
        "state": -44.0,
        "carryover": -224.68999999999983,
    },
    {
        "envelope": "Haushalt:Lebensmittel",
        "month": "2024-01",
        "budget": 1250.0,
        "state_month": 1250.0,
        "state": 1206.0,
        "carryover": -43.539999999999736,
    },
    {
        "envelope": "Haushalt:Sonstiges",
        "month": "2023-10",
        "budget": 70.0,
        "state_month": -71.0,
        "state": -71.0,
        "carryover": None,
    },
    {
        "envelope": "Haushalt:Sonstiges",
        "month": "2023-11",
        "budget": 70.0,
        "state_month": 48.0,
        "state": -23.0,
        "carryover": -71.44999999999999,
    },
    {
        "envelope": "Haushalt:Sonstiges",
        "month": "2023-12",
        "budget": 70.0,
        "state_month": -43.0,
        "state": -66.0,
        "carryover": -23.19999999999999,
    },
    {
        "envelope": "Haushalt:Sonstiges",
        "month": "2024-01",
        "budget": 70.0,
        "state_month": 70.0,
        "state": 4.0,
        "carryover": -65.99999999999999,
    },
    {
        "envelope": "Privat",
        "month": "2023-10",
        "budget": 230.0,
        "state_month": -82.0,
        "state": -82.0,
        "carryover": None,
    },
    {
        "envelope": "Privat",
        "month": "2023-11",
        "budget": 730.0,
        "state_month": 227.0,
        "state": 145.0,
        "carryover": -82.30000000000001,
    },
    {
        "envelope": "Privat",
        "month": "2023-12",
        "budget": 330.0,
        "state_month": -168.0,
        "state": -23.0,
        "carryover": 144.52000000000004,
    },
    {
        "envelope": "Privat",
        "month": "2024-01",
        "budget": 230.0,
        "state_month": 230.0,
        "state": 207.0,
        "carryover": -23.049999999999955,
    },
    {
        "envelope": "Privat:Geschenke",
        "month": "2023-10",
        "budget": 130.0,
        "state_month": -102.0,
        "state": -102.0,
        "carryover": None,
    },
    {
        "envelope": "Privat:Geschenke",
        "month": "2023-11",
        "budget": 630.0,
        "state_month": 270.0,
        "state": 168.0,
        "carryover": -101.75,
    },
    {
        "envelope": "Privat:Geschenke",
        "month": "2023-12",
        "budget": 230.0,
        "state_month": -164.0,
        "state": 4.0,
        "carryover": 168.37,
    },
    {
        "envelope": "Privat:Geschenke",
        "month": "2024-01",
        "budget": 130.0,
        "state_month": 130.0,
        "state": 134.0,
        "carryover": 4.399999999999977,
    },
    {
        "envelope": "Privat:Werbungskosten",
        "month": "2023-10",
        "budget": 100.0,
        "state_month": 19.0,
        "state": 19.0,
        "carryover": None,
    },
    {
        "envelope": "Privat:Werbungskosten",
        "month": "2023-11",
        "budget": 100.0,
        "state_month": -43.0,
        "state": -24.0,
        "carryover": 19.450000000000003,
    },
    {
        "envelope": "Privat:Werbungskosten",
        "month": "2023-12",
        "budget": 100.0,
        "state_month": 36.0,
        "state": 13.0,
        "carryover": -23.85000000000001,
    },
    {
        "envelope": "Privat:Werbungskosten",
        "month": "2024-01",
        "budget": 100.0,
        "state_month": 100.0,
        "state": 113.0,
        "carryover": 12.54999999999999,
    },
    {
        "envelope": "Privat:Werbungskosten:Essen+Kaffee",
        "month": "2023-10",
        "budget": 100.0,
        "state_month": 19.0,
        "state": 19.0,
        "carryover": None,
    },
    {
        "envelope": "Privat:Werbungskosten:Essen+Kaffee",
        "month": "2023-11",
        "budget": 100.0,
        "state_month": -43.0,
        "state": -24.0,
        "carryover": 19.450000000000003,
    },
    {
        "envelope": "Privat:Werbungskosten:Essen+Kaffee",
        "month": "2023-12",
        "budget": 100.0,
        "state_month": 36.0,
        "state": 13.0,
        "carryover": -23.85000000000001,
    },
    {
        "envelope": "Privat:Werbungskosten:Essen+Kaffee",
        "month": "2024-01",
        "budget": 100.0,
        "state_month": 100.0,
        "state": 113.0,
        "carryover": 12.54999999999999,
    },
    {
        "envelope": "Umbuchung",
        "month": "2023-10",
        "budget": 1630.0,
        "state_month": 100.0,
        "state": 100.0,
        "carryover": None,
    },
    {
        "envelope": "Umbuchung",
        "month": "2023-11",
        "budget": 1630.0,
        "state_month": 100.0,
        "state": 200.0,
        "carryover": 100.0,
    },
    {
        "envelope": "Umbuchung",
        "month": "2023-12",
        "budget": 1746.0,
        "state_month": -198.0,
        "state": 2.0,
        "carryover": 200.0,
    },
    {
        "envelope": "Umbuchung",
        "month": "2024-01",
        "budget": 1630.0,
        "state_month": 1390.0,
        "state": 1392.0,
        "carryover": 2.4700000000000273,
    },
    {
        "envelope": "Umbuchung:R\u00fcckstellungen",
        "month": "2023-10",
        "budget": 230.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": None,
    },
    {
        "envelope": "Umbuchung:R\u00fcckstellungen",
        "month": "2023-11",
        "budget": 230.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": 0.0,
    },
    {
        "envelope": "Umbuchung:R\u00fcckstellungen",
        "month": "2023-12",
        "budget": 230.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": 0.0,
    },
    {
        "envelope": "Umbuchung:R\u00fcckstellungen",
        "month": "2024-01",
        "budget": 230.0,
        "state_month": -10.0,
        "state": -10.0,
        "carryover": 0.0,
    },
    {
        "envelope": "Umbuchung:Sparen",
        "month": "2023-10",
        "budget": 1100.0,
        "state_month": 100.0,
        "state": 100.0,
        "carryover": None,
    },
    {
        "envelope": "Umbuchung:Sparen",
        "month": "2023-11",
        "budget": 1100.0,
        "state_month": 100.0,
        "state": 200.0,
        "carryover": 100.0,
    },
    {
        "envelope": "Umbuchung:Sparen",
        "month": "2023-12",
        "budget": 1216.0,
        "state_month": -200.0,
        "state": -0.0,
        "carryover": 200.0,
    },
    {
        "envelope": "Umbuchung:Sparen",
        "month": "2024-01",
        "budget": 1100.0,
        "state_month": 1100.0,
        "state": 1100.0,
        "carryover": -0.11999999999989086,
    },
    {
        "envelope": "Umbuchung:Taschengeld",
        "month": "2023-10",
        "budget": 300.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": None,
    },
    {
        "envelope": "Umbuchung:Taschengeld",
        "month": "2023-11",
        "budget": 300.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": 0.0,
    },
    {
        "envelope": "Umbuchung:Taschengeld",
        "month": "2023-12",
        "budget": 300.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": 0.0,
    },
    {
        "envelope": "Umbuchung:Taschengeld",
        "month": "2024-01",
        "budget": 300.0,
        "state_month": 300.0,
        "state": 300.0,
        "carryover": 0.0,
    },
    {
        "envelope": "Urlaub",
        "month": "2023-10",
        "budget": 250.0,
        "state_month": 24.0,
        "state": 24.0,
        "carryover": None,
    },
    {
        "envelope": "Urlaub",
        "month": "2023-11",
        "budget": 250.0,
        "state_month": 250.0,
        "state": 274.0,
        "carryover": 23.80000000000001,
    },
    {
        "envelope": "Urlaub",
        "month": "2023-12",
        "budget": 250.0,
        "state_month": 250.0,
        "state": 524.0,
        "carryover": 273.8,
    },
    {
        "envelope": "Urlaub",
        "month": "2024-01",
        "budget": 250.0,
        "state_month": 250.0,
        "state": 774.0,
        "carryover": 523.8,
    },
    {
        "envelope": "Verkehrsmittel",
        "month": "2023-10",
        "budget": 70.0,
        "state_month": -25.0,
        "state": -25.0,
        "carryover": None,
    },
    {
        "envelope": "Verkehrsmittel",
        "month": "2023-11",
        "budget": 70.0,
        "state_month": 20.0,
        "state": -5.0,
        "carryover": -25.299999999999997,
    },
    {
        "envelope": "Verkehrsmittel",
        "month": "2023-12",
        "budget": 70.0,
        "state_month": 13.0,
        "state": 9.0,
        "carryover": -4.8999999999999915,
    },
    {
        "envelope": "Verkehrsmittel",
        "month": "2024-01",
        "budget": 70.0,
        "state_month": 70.0,
        "state": 79.0,
        "carryover": 8.500000000000014,
    },
    {
        "envelope": "Wohnen",
        "month": "2023-10",
        "budget": 2987.0,
        "state_month": 22.0,
        "state": 22.0,
        "carryover": None,
    },
    {
        "envelope": "Wohnen",
        "month": "2023-11",
        "budget": 3139.0,
        "state_month": 10.0,
        "state": 32.0,
        "carryover": 22.159999999999854,
    },
    {
        "envelope": "Wohnen",
        "month": "2023-12",
        "budget": 3218.0,
        "state_month": 87.0,
        "state": 120.0,
        "carryover": 32.36999999999989,
    },
    {
        "envelope": "Wohnen",
        "month": "2024-01",
        "budget": 3139.0,
        "state_month": 184.0,
        "state": 304.0,
        "carryover": 119.52999999999975,
    },
    {
        "envelope": "Wohnen:Bekleidung",
        "month": "2023-12",
        "budget": 20.0,
        "state_month": 20.0,
        "state": 20.0,
        "carryover": 0.0,
    },
    {
        "envelope": "Wohnen:Haushaltsger\u00e4te",
        "month": "2023-10",
        "budget": 17.0,
        "state_month": 17.0,
        "state": 17.0,
        "carryover": None,
    },
    {
        "envelope": "Wohnen:Haushaltsger\u00e4te",
        "month": "2023-11",
        "budget": 17.0,
        "state_month": 17.0,
        "state": 34.0,
        "carryover": 17.0,
    },
    {
        "envelope": "Wohnen:Haushaltsger\u00e4te",
        "month": "2023-12",
        "budget": 17.0,
        "state_month": 17.0,
        "state": 51.0,
        "carryover": 34.0,
    },
    {
        "envelope": "Wohnen:Haushaltsger\u00e4te",
        "month": "2024-01",
        "budget": 17.0,
        "state_month": 17.0,
        "state": 68.0,
        "carryover": 51.0,
    },
    {
        "envelope": "Wohnen:Inneneinrichtung",
        "month": "2023-10",
        "budget": 50.0,
        "state_month": 1.0,
        "state": 1.0,
        "carryover": None,
    },
    {
        "envelope": "Wohnen:Inneneinrichtung",
        "month": "2023-11",
        "budget": 50.0,
        "state_month": 8.0,
        "state": 9.0,
        "carryover": 0.7999999999999972,
    },
    {
        "envelope": "Wohnen:Inneneinrichtung",
        "month": "2023-12",
        "budget": 50.0,
        "state_month": -11.0,
        "state": -2.0,
        "carryover": 8.899999999999999,
    },
    {
        "envelope": "Wohnen:Inneneinrichtung",
        "month": "2024-01",
        "budget": 50.0,
        "state_month": 50.0,
        "state": 48.0,
        "carryover": -2.4499999999999957,
    },
    {
        "envelope": "Wohnen:Instandhaltung",
        "month": "2023-10",
        "budget": 17.0,
        "state_month": 17.0,
        "state": 17.0,
        "carryover": None,
    },
    {
        "envelope": "Wohnen:Instandhaltung",
        "month": "2023-11",
        "budget": 17.0,
        "state_month": 17.0,
        "state": 34.0,
        "carryover": 17.0,
    },
    {
        "envelope": "Wohnen:Instandhaltung",
        "month": "2023-12",
        "budget": 17.0,
        "state_month": 17.0,
        "state": 51.0,
        "carryover": 34.0,
    },
    {
        "envelope": "Wohnen:Instandhaltung",
        "month": "2024-01",
        "budget": 17.0,
        "state_month": 17.0,
        "state": 68.0,
        "carryover": 51.0,
    },
    {
        "envelope": "Wohnen:Miete",
        "month": "2023-10",
        "budget": 2710.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": None,
    },
    {
        "envelope": "Wohnen:Miete",
        "month": "2023-11",
        "budget": 2862.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": 0.0,
    },
    {
        "envelope": "Wohnen:Miete",
        "month": "2023-12",
        "budget": 2862.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": 0.0,
    },
    {
        "envelope": "Wohnen:Miete",
        "month": "2024-01",
        "budget": 2862.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": 0.0,
    },
    {
        "envelope": "Wohnen:Nebenkosten",
        "month": "2023-10",
        "budget": 93.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": None,
    },
    {
        "envelope": "Wohnen:Nebenkosten",
        "month": "2023-11",
        "budget": 93.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": 0.0,
    },
    {
        "envelope": "Wohnen:Nebenkosten",
        "month": "2023-12",
        "budget": 93.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": 0.0,
    },
    {
        "envelope": "Wohnen:Nebenkosten",
        "month": "2024-01",
        "budget": 93.0,
        "state_month": 0.0,
        "state": 0.0,
        "carryover": 0.0,
    },
    {
        "envelope": "Wohnen:Telefon+Internet",
        "month": "2023-10",
        "budget": 100.0,
        "state_month": -13.0,
        "state": -13.0,
        "carryover": None,
    },
    {
        "envelope": "Wohnen:Telefon+Internet",
        "month": "2023-11",
        "budget": 100.0,
        "state_month": -32.0,
        "state": -45.0,
        "carryover": -12.64,
    },
    {
        "envelope": "Wohnen:Telefon+Internet",
        "month": "2023-12",
        "budget": 159.0,
        "state_month": 45.0,
        "state": -0.0,
        "carryover": -44.52999999999999,
    },
    {
        "envelope": "Wohnen:Telefon+Internet",
        "month": "2024-01",
        "budget": 100.0,
        "state_month": 100.0,
        "state": 100.0,
        "carryover": -0.01999999999998181,
    },
]
