from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.template import result_as_boolean

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
        RscEntityDefinition(
            RscEntityType.BINARY_SENSOR, RscBinarySensor, async_add_entities
        )
    )


class RscBinarySensor(BinarySensorEntity, RscEntity):
    @property
    def is_on(self) -> bool | None:
        """Return the state, text from a template is parsed by HA's result_as_boolean."""
        value = self.rsc_value
        if value is None:
            return None
        return result_as_boolean(value)
