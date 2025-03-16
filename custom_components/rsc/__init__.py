import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from . import const
from .devices.rsc_manager import RscManager
from .entities.rsc_entities_manager import RscEntitiesManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up integration from a config entry."""

    hass.data.setdefault(const.DOMAIN, {})[entry.entry_id] = {}
    # Forward setup for the sensor platform

    entities_manager = RscEntitiesManager()
    hass.data[const.DOMAIN][entry.entry_id][const.ENTITIES_MANAGER] = entities_manager

    await hass.config_entries.async_forward_entry_setups(
        entry,
        ["sensor", "switch", "binary_sensor", "cover", "button", "number"],
    )

    rsc_manager = RscManager(Path(hass.config.path("rsc.yaml")), entities_manager)
    if not rsc_manager.load_config():
        _LOGGER.error("Failed to load configuration")
        return False

    rsc_manager.start_all_masters()
    hass.data[const.DOMAIN][entry.entry_id][const.RSC_MANAGER] = rsc_manager

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""

    rsc_manager: RscManager = (
        hass.data[const.DOMAIN].pop(entry.entry_id).get(const.RSC_MANAGER)
    )
    if rsc_manager:
        rsc_manager.stop_all_masters()

    hass.data[const.DOMAIN].pop(entry.entry_id, None)
    return True
