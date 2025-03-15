from .rsc_entity_type import RscEntityType
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .rsc_entity import RscEntity


class RscEntityDefinition:
    def __init__(
        self,
        entity_type: RscEntityType,
        create_entity: type[RscEntity],
        async_add_entities: AddEntitiesCallback,
    ):
        self.entity_type = entity_type
        self.create_entity = create_entity
        self.async_add_entities = async_add_entities
