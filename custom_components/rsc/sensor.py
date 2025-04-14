from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

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

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.rsc_value

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit

    @property
    def state_class(self):
        """Return the state class of the sensor."""
        return SensorStateClass.MEASUREMENT
