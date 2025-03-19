from abc import ABC, abstractmethod
import logging
import threading
from typing import Any

from jinja2 import Environment

from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import run_callback_threadsafe

from .. import const
from ..devices.ios.abstract.rsc_input import RscInput
from ..devices.ios.abstract.rsc_output import RscOutput

_LOGGER = logging.getLogger(__name__)


class RscEntity(ABC, Entity):
    def __init__(
        self,
        config: dict[str, Any],
        rsc_input: RscInput = None,
        rsc_output: RscOutput = None,
    ):
        super().__init__()
        self.rsc_value = None
        self._init_from_config(config)
        if (rsc_input is None) and (rsc_output is None):
            raise ValueError("Either rsc_input or rsc_output must be provided")
        self._rsc_input = rsc_input
        self._rsc_output = rsc_output

        self._update_rsc_value()

    def _init_from_config(self, config: dict[str, Any]) -> None:
        """Initialize the entity from the configuration."""
        self._config = config

        self._id: str = config.get("id")
        if not self._id:
            raise ValueError("ID is required in the configuration")

        self._name: str = config.get("title", self._id)
        self._template: str | None = config.get("template")
        self._unit: str | None = config.get("unit")

        device_class = config.get("device_class", self._default_device_class())
        if device_class:
            self._attr_device_class = device_class

        entity_category = config.get("entity_category")
        if entity_category:
            self._attr_entity_category = EntityCategory(entity_category)

    def _default_device_class(self) -> str | None:
        return None

    @property
    def device_info(self):
        return {
            "identifiers": {(const.DOMAIN, self._config["device_uid"])},
        }

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def suggested_object_id(self):
        """Return the suggested object id."""
        return self._id

    @property
    def unique_id(self):
        """Return a unique ID for the sensor."""
        return self._id

    @property
    def available(self):
        """Return True if the sensor is available."""
        return (self._rsc_input.is_online if self._rsc_input else True) and (
            self._rsc_output.is_online if self._rsc_output else True
        )

    def _update_rsc_value(self):
        raw_value = self._rsc_input.value if self._rsc_input else self._rsc_output.value
        if self._template:
            try:
                env = Environment()
                template = env.from_string(self._template)
                self.rsc_value = template.render(value=raw_value)
            except Exception as e:
                _LOGGER.error(
                    f"Error rendering template for entity: {self._name}. Error: {self._template}: {e}"
                )
                self.rsc_value = raw_value
        else:
            self.rsc_value = raw_value

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attributes = {}

        # Merge attributes from input if available
        if self._rsc_input and self._rsc_input.attributes:
            attributes.update(self._rsc_input.attributes)

        # Merge attributes from output if available
        if self._rsc_output and self._rsc_output.attributes:
            attributes.update(self._rsc_output.attributes)

        return attributes if attributes else None

    def io_changed(self):
        """Handle changes in IO states."""

        self._update_rsc_value()

        if threading.current_thread() is threading.main_thread():
            self.async_write_ha_state()
        else:
            run_callback_threadsafe(self.hass.loop, self.async_write_ha_state)

    def set_io(self, value):
        """Set the value of the IO."""
        if self._rsc_output is None:
            raise ValueError("RscOutput is not set")

        self._rsc_output.value = value
