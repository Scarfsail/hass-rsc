import time

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later

from . import const
from .entities import RscEntitiesManager, RscEntity, RscEntityDefinition, RscEntityType


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up CentralDvc sensors from a config entry."""
    mgr: RscEntitiesManager = hass.data[const.DOMAIN][entry.entry_id][
        const.ENTITIES_MANAGER
    ]
    mgr.register_entity_type(
        RscEntityDefinition(RscEntityType.SENSOR, RscSensor, async_add_entities)
    )


class RscSensor(SensorEntity, RscEntity):
    def __init__(self, *args):
        super().__init__(*args)
        # Set precision to 1 decimal place by default, or use config value if provided

        self._attr_native_precision = self._config.get("precision", 1)

        # Throttling of state writes, touched only on the event loop
        self._threshold = self._config.get("threshold")
        self._last_write: float | None = None
        self._last_state = None
        self._last_available = None
        self._cancel_flush = None

    def _min_interval(self) -> float:
        """Return the minimal interval between state writes in seconds."""
        fast_mode_io = self._config.get("fast_mode_io")
        if fast_mode_io and fast_mode_io.value:
            return 0
        return self._config["min_interval"]

    @callback
    def _async_handle_io_changed(self):
        """Publish the new state at most once per min_interval."""
        state = self.state
        now = time.monotonic()

        if (
            self._last_write is None
            or self.available != self._last_available
            or not isinstance(state, (int, float))
            or not isinstance(self._last_state, (int, float))
            or (
                self._threshold is not None
                and abs(state - self._last_state) >= self._threshold
            )
            or now - self._last_write >= self._min_interval()
        ):
            self._async_write_and_record()
        elif self._cancel_flush is None:
            self._cancel_flush = async_call_later(
                self.hass,
                self._last_write + self._min_interval() - now,
                self._async_flush,
            )

    @callback
    def _async_flush(self, _now):
        self._cancel_flush = None
        self._async_write_and_record()

    @callback
    def _async_write_and_record(self):
        self.async_write_ha_state()
        self._last_write = time.monotonic()
        self._last_state = self.state
        self._last_available = self.available
        self._async_cancel_flush()

    @callback
    def _async_cancel_flush(self):
        if self._cancel_flush is not None:
            self._cancel_flush()
            self._cancel_flush = None

    async def async_will_remove_from_hass(self):
        """Cancel a pending trailing flush."""
        self._async_cancel_flush()
        await super().async_will_remove_from_hass()

    @property
    def state(self):
        """Return the state of the sensor."""
        if self.rsc_value is None or isinstance(self.rsc_value, int):
            return self.rsc_value

        value = self.rsc_value

        if isinstance(self.rsc_value, str):
            try:
                value = float(self.rsc_value)
            except ValueError:
                return self.rsc_value

        return round(value, self._attr_native_precision)

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def state_class(self):
        """Return the state class of the sensor."""
        return SensorStateClass.MEASUREMENT
