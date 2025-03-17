from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
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
        RscEntityDefinition(RscEntityType.SWITCH, RscSwitch, async_add_entities)
    )


class RscSwitch(SwitchEntity, RscEntity):
    def _default_device_class(self):
        """Return the device class of the switch."""
        return SwitchDeviceClass.OUTLET

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
