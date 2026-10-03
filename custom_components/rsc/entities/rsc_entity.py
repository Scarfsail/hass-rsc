from abc import ABC, abstractmethod
import asyncio
import logging
import threading
from typing import Any

from jinja2 import StrictUndefined, Template, Undefined
from jinja2.nativetypes import NativeEnvironment

from homeassistant.const import EntityCategory
from homeassistant.core import callback
from homeassistant.helpers.entity import Entity

from .. import const
from ..devices.ios.abstract.rsc_input import RscInput
from ..devices.ios.abstract.rsc_output import RscOutput

_LOGGER = logging.getLogger(__name__)

# Renders to native Python values (False, -87.6, ...), undefined variables raise
_TEMPLATE_ENV = NativeEnvironment(undefined=StrictUndefined)

# Coalesces IO changes from the worker threads into one event loop callback per burst
_pending_lock = threading.Lock()
_pending_entities: set["RscEntity"] = set()
_flush_scheduled = False


def _queue_io_changed(entity: "RscEntity", loop: asyncio.AbstractEventLoop) -> None:
    """Queue the entity for a state write on the event loop, runs in a worker thread."""
    global _flush_scheduled
    with _pending_lock:
        _pending_entities.add(entity)
        if _flush_scheduled:
            return
        _flush_scheduled = True
    try:
        loop.call_soon_threadsafe(_flush_io_changed)
    except RuntimeError:
        # Event loop is closed (HA is stopping), don't leave the flush flag stuck
        with _pending_lock:
            _flush_scheduled = False


@callback
def _flush_io_changed() -> None:
    """Publish the states of all queued entities, runs on the event loop."""
    global _pending_entities, _flush_scheduled
    with _pending_lock:
        entities = _pending_entities
        _pending_entities = set()
        _flush_scheduled = False
    for entity in entities:
        if entity.hass is None:
            continue
        try:
            entity._async_handle_io_changed()
        except Exception:
            # One failing entity must not drop the state writes of the others
            _LOGGER.exception(f"Error writing state of entity: {entity.entity_id}")


class RscEntity(ABC, Entity):
    # State is pushed from io_changed(), HA polling would bypass sensor throttling
    _attr_should_poll = False

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
        self._template: Template | None = None
        template = config.get("template")
        if template:
            try:
                self._template = _TEMPLATE_ENV.from_string(template)
            except Exception as e:
                _LOGGER.error(
                    f"Invalid template for entity: {self._name}, raw value is used. Error: {template}: {e}"
                )
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
                rendered = self._template.render(value=raw_value)
                if isinstance(rendered, Undefined):
                    # A lone {{ undefined_var }} is returned as is, not raised
                    raise ValueError("template rendered an undefined value")
                self.rsc_value = rendered
            except Exception as e:
                _LOGGER.error(
                    f"Error rendering template for entity: {self._name}. Error: {self._config['template']}: {e}"
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

        hass = self.hass
        if hass is None:
            # Not added to HA yet (or disabled), the initial write picks up the value
            return

        if threading.current_thread() is threading.main_thread():
            self._async_handle_io_changed()
        else:
            _queue_io_changed(self, hass.loop)

    @callback
    def _async_handle_io_changed(self):
        """Publish the new state, runs on the event loop."""
        self.async_write_ha_state()

    def set_io(self, value):
        """Set the value of the IO."""
        if self._rsc_output is None:
            raise ValueError("RscOutput is not set")

        self._rsc_output.value = value
