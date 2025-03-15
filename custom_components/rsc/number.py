from config.custom_components.rsc.entities.rsc_entity_type import RscEntityType
from homeassistant.components.number import NumberEntity
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
        RscEntityDefinition(RscEntityType.NUMBER, RscNumber, async_add_entities)
    )


class RscNumber(NumberEntity, RscEntity):
    @property
    def step(self):
        """Return the step value."""
        return 1

    @property
    def value(self):
        """Return the current value."""
        return self.rsc_value

    def set_value(self, value):
        """Turn the entity on."""
        self.set_io(value)
