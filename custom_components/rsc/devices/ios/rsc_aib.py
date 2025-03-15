import logging

from .abstract.rsc_io_type import RscIoType
from .rsc_ai import RscAi

_LOGGER = logging.getLogger(__name__)


class RscAib(RscAi):
    def __init__(self, io_index: int, title: str, units: str, default_value: int = 0):
        super().__init__(io_index, title, units, default_value)

    def get_io_type_id(self) -> RscIoType:
        return RscIoType.AIB

    def get_io_data_length(self) -> int:
        return 1

    def _process_value(self, data: bytes, position: int) -> int:
        return data[position]
