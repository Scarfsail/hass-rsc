from abc import ABC, abstractmethod
from typing import TypeVar
from .rsc_io_type import RscIoType

T = TypeVar("T")


class RscIo(ABC):
    def __init__(self, io_index: int, title: str, default_value):
        self.io_index = io_index
        self.title = title

        self.value = default_value
        self.is_online = False

    def _on_value_changed(self) -> None:
        pass

    @abstractmethod
    def get_io_data_length(self) -> int:
        """Get the length of IO data in bytes."""

    @abstractmethod
    def get_io_type_id(self) -> RscIoType:
        """Get the IO type ID."""
