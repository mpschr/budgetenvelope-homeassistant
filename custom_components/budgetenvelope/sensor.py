"""Sensor integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import BudgetEnvelopeBaseEntity, get_object_value
from .const import DOMAIN


@dataclass
class BudgetEnvelopeEntityDescription(SensorEntityDescription):
    """Describes Volkswagen ID sensor entity."""

    value: Callable = lambda x, y: x


SENSORS: tuple[BudgetEnvelopeEntityDescription, ...] = [
    (
        BudgetEnvelopeEntityDescription(
            key="Balance",
            name="Balance",
            icon="mdi:cash-multiple",
            value=lambda data: data["state"],
            suggested_display_precision=0,
            device_class=SensorDeviceClass.MONETARY,
            native_unit_of_measurement="CHF",
        )
    ),
    (
        BudgetEnvelopeEntityDescription(
            key="Balance Percent",
            name="Balance Percent",
            icon="mdi:cash-multiple",
            value=lambda data: data["state_percentage"],
            suggested_display_precision=0,
            device_class=SensorDeviceClass.BATTERY,
            native_unit_of_measurement=PERCENTAGE,
        )
    ),
    (
        BudgetEnvelopeEntityDescription(
            key="Budget",
            name="Budget",
            icon="mdi:wallet-outline",
            value=lambda data: data["budget"],
            suggested_display_precision=0,
            device_class=SensorDeviceClass.MONETARY,
            native_unit_of_measurement="CHF",
        )
    ),
    (
        BudgetEnvelopeEntityDescription(
            key="Adjustment",
            name="Adjustment",
            icon="mdi:wallet-outline",
            value=lambda data: data["adjustment"],
            suggested_display_precision=0,
            device_class=SensorDeviceClass.MONETARY,
            native_unit_of_measurement="CHF",
        )
    ),    
    (
        BudgetEnvelopeEntityDescription(
            key="Carryover",
            name="Carryover",
            icon="mdi:hand-coin-outline",
            value=lambda data: data["carryover"],
            suggested_display_precision=0,
            device_class=SensorDeviceClass.MONETARY,
            native_unit_of_measurement="CHF",
        )
    ),
]


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Add sensors for passed config_entry in HA."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id + "_coordinator"]

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_config_entry_first_refresh()

    entities: list[BudgetEnvelopeSensor] = []

    # for index, vehicle in enumerate(coordinator.data):
    for key in coordinator.data:
        for sensor in SENSORS:
            entities.append(BudgetEnvelopeSensor(sensor, coordinator, key))

    if entities:
        async_add_entities(entities)


class BudgetEnvelopeSensor(BudgetEnvelopeBaseEntity, SensorEntity):
    """Representation of a VolkswagenID vehicle sensor."""

    entity_description: BudgetEnvelopeEntityDescription

    def __init__(
        self,
        sensor: BudgetEnvelopeEntityDescription,
        coordinator: DataUpdateCoordinator,
        index: int,
    ) -> None:
        """Initialize VolkswagenID vehicle sensor."""
        super().__init__(coordinator, index)

        self.entity_description = sensor
        self._coordinator = coordinator
        self._attr_name = f"{self.data['envelope']} {sensor.name}"
        self._attr_unique_id = f"envbudget-{self.data['envelope']}-{sensor.key}"
        if sensor.native_unit_of_measurement:
            self._attr_native_unit_of_measurement = sensor.native_unit_of_measurement
        #    self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self) -> StateType:
        """Return the state."""

        try:
            state = get_object_value(self.entity_description.value(self.data))
        except (KeyError, ValueError):
            return None

        return cast(StateType, state)
