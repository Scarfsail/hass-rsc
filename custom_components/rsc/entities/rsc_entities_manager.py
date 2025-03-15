import logging
from typing import Any

from .rsc_entity import RscEntity

from ..devices.ios.abstract.rsc_io import RscIo

from ..devices.ios.abstract.rsc_input import RscInput
from ..devices.ios.abstract.rsc_output import RscOutput
from .rsc_entity_type import RscEntityType
from .rsc_entity_definition import RscEntityDefinition

_LOGGER = logging.getLogger(__name__)


class EntityConfigWithIo:
    def __init__(
        self, config: dict[str, Any], rsc_input: RscInput, rsc_output: RscOutput
    ):
        self.config = config
        self.rsc_input = rsc_input
        self.rsc_output = rsc_output
        self.entities: list[RscEntity] = []


class RscEntitiesManager:
    def __init__(self):
        self.entity_definitions: dict[RscEntityType, RscEntityDefinition] = {}
        self.entity_configs: dict[str, EntityConfigWithIo] = {}

    def register_entity_type(self, definition: RscEntityDefinition):
        """Register an entity type with the manager."""
        if definition.entity_type in self.entity_definitions:
            raise ValueError(
                f"Entity type {definition.entity_type} already registered."
            )

        # Register the entity type
        self.entity_definitions[definition.entity_type] = definition
        _LOGGER.debug(f"Registered entity type: {definition.entity_type}")

    def register_entity_config(self, config: dict[str, Any], rsc_io: RscIo):
        if "id" not in config:
            raise ValueError("Config must contain 'id'.")
        if not rsc_io:
            raise ValueError("rsc_io must be provided.")

        rsc_input = rsc_io if isinstance(rsc_io, RscInput) else None
        rsc_output = rsc_io if isinstance(rsc_io, RscOutput) else None

        id = config["id"]

        if id not in self.entity_configs:
            self.entity_configs[id] = EntityConfigWithIo(config, rsc_input, rsc_output)
            _LOGGER.debug(f"Registered entity config: {config['id']}")
        else:
            cfg = self.entity_configs[id]
            cfg.config.update(config)
            if rsc_input:
                cfg.rsc_input = rsc_input
            if rsc_output:
                cfg.rsc_output = rsc_output
            _LOGGER.debug(f"Updated entity config: {config['id']}")

    def create_entities(self):
        """Create entities based on the registered configurations."""
        for entity_config in self.entity_configs.values():
            config = entity_config.config
            rsc_input = entity_config.rsc_input
            rsc_output = entity_config.rsc_output

            entity_type = RscEntityType(config.get("type"))

            if entity_type not in self.entity_definitions:
                _LOGGER.error(f"Entity type {entity_type} not registered.")
                continue

            definition = self.entity_definitions[entity_type]
            entity = definition.create_entity(config, rsc_input, rsc_output)
            definition.async_add_entities([entity])
            if entity:
                entity_config.entities.append(entity)

                if rsc_input:
                    rsc_input.register_entity(entity)

                if rsc_output:
                    rsc_output.register_entity(entity)

                _LOGGER.debug(f"Created entity: {entity}")
