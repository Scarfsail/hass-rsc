import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .devices.rsc_manager import RscManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up integration from a config entry."""

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {}

    rsc_manager = RscManager(Path(hass.config.path("rsc.yaml")))
    if not rsc_manager.load_config():
        _LOGGER.error("Failed to load configuration")
        return False

    rsc_manager.start_all_masters()

    hass.data[DOMAIN][entry.entry_id]["rsc_manager"] = rsc_manager
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""

    rsc_manager: RscManager = hass.data[DOMAIN].pop(entry.entry_id).get("rsc_manager")
    if rsc_manager:
        rsc_manager.stop_all_masters()

    hass.data[DOMAIN].pop(entry.entry_id, None)
    return True
