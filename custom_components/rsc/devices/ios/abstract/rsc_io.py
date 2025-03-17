from abc import ABC, abstractmethod

# from ....entities.rsc_entity import RscEntity

from .rsc_io_type import RscIoType


class RscIo(ABC):
    def __init__(self, io_index: int, title: str, default_value):
        self.io_index = io_index
        self.title = title

        self._value = default_value
        self._is_online = False
        self._entities = []
        self._first_time_value_set = False

    def _on_changed(self) -> None:
        """Notify all registered entities of a change."""
        for entity in self._entities:
            entity.io_changed()

    def _on_is_online_change(self) -> None:
        """Handle changes to the online status."""
        pass

    @property
    def value(self):
        """Get the current value."""
        return self._value

    @value.setter
    def value(self, value) -> None:
        """Set the value and notify if it has changed."""
        if self._value != value:  # or not self._first_time_value_set:
            self._first_time_value_set = True
            self._value = value
            self._on_changed()

    @property
    def is_online(self) -> bool:
        """Check if the IO is online."""
        return self._is_online

    @is_online.setter
    def is_online(self, value: bool) -> None:
        """Set the online status."""
        if self._is_online != value:
            self._is_online = value
            self._on_is_online_change()
            self._on_changed()

    def register_entity(self, entity) -> None:
        """Register an entity to be notified of changes."""
        self._entities.append(entity)

    @abstractmethod
    def get_io_data_length(self) -> int:
        """Get the length of IO data in bytes."""

    @abstractmethod
    def get_io_type_id(self) -> RscIoType:
        """Get the IO type ID."""
