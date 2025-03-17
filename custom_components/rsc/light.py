from homeassistant.components.light import ColorMode, LightEntity
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
        RscEntityDefinition(RscEntityType.LIGHT, RscLight, async_add_entities)
    )


class RscLight(LightEntity, RscEntity):
    def __init__(self, *args):
        super().__init__(*args)
        self._attr_supported_color_modes = [ColorMode.ONOFF]
        self._attr_color_mode = ColorMode.ONOFF

    @property
    def is_on(self):
        """Return the state of the switch."""
        return self.rsc_value

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        self.set_io(True)

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        self.set_io(False)
