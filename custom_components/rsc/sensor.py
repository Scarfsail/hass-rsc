from config.custom_components.rsc.entities.rsc_entity_type import RscEntityType
from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import const
from .entities.rsc_entities_manager import RscEntitiesManager
from .entities.rsc_entity import RscEntity
from .entities.rsc_entity_definition import RscEntityDefinition


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
    @property
    def state(self):
        """Return the state of the sensor."""
        return self.value

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self.unit

    @property
    def state_class(self):
        """Return the state class of the sensor."""
        return SensorStateClass.MEASUREMENT
