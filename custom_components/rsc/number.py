from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import const
from .entities.rsc_entities_manager import RscEntitiesManager
from .entities.rsc_entity import RscEntity
from .entities.rsc_entity_definition import RscEntityDefinition
from .entities.rsc_entity_type import RscEntityType


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
    def __init__(self, config, rsc_input=None, rsc_output=None):
        super().__init__(config, rsc_input, rsc_output)
        min_value = config.get("min", None)
        if min_value is not None:
            self._attr_native_min_value = min_value
        max_value = config.get("max", None)
        if max_value is not None:
            self._attr_native_max_value = max_value

        self._attr_native_step = self._config.get("step", 1)

    @property
    def value(self):
        """Return the current value."""
        return self.rsc_value

    def set_value(self, value):
        """Set the entity's value."""
        self.set_io(value)
