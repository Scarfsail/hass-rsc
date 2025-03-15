from config.custom_components.rsc.entities.rsc_entity_type import RscEntityType
from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
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
        RscEntityDefinition(RscEntityType.GATE, RscGate, async_add_entities)
    )


class RscGate(CoverEntity, RscEntity):
    def _default_device_class(self):
        return CoverDeviceClass.GARAGE

    @property
    def supported_features(self):
        """Flag supported features."""
        return (
            CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
        )

    @property
    def is_closed(self):
        """Return the state of the sensor."""
        return self.rsc_value == 0

    @property
    def is_closing(self):
        """Return the state of the sensor."""
        return self.rsc_value == 3

    @property
    def is_opening(self):
        """Return the state of the sensor."""
        return self.rsc_value == 4

    @property
    def current_cover_position(self):
        """Return the state of the sensor."""
        match self.rsc_value:
            case 0:  # Closed
                return 0
            case 1:  # OpenedPartially
                return 50
            case 2:  # OpenedFully
                return 100
            case 3:  # Closing
                return 50
            case 4:  # Opening
                return 50
            case _:
                return 100

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        self.set_io(1)

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        self.set_io(2)

    async def async_close_cover(self, **kwargs):
        """Close the cover."""
        self.set_io(3)
