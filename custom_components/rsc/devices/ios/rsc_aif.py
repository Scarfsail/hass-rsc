import struct

from .abstract.rsc_io_type import RscIoType
from .rsc_ai import RscAi


class RscAif(RscAi):
    def __init__(
        self, io_index: int, title: str, units: str, default_value: float = 0.0
    ):
        super().__init__(io_index, title, units, default_value)

    def get_io_type_id(self) -> RscIoType:
        return RscIoType.AIF

    def get_io_data_length(self) -> int:
        return 4

    def _process_value(self, data: bytes, position: int) -> float:
        return struct.unpack("<f", data[position : position + 4])[0]

    def _is_processed_value_valid(self, value: float) -> bool:
        return not (value != value)  # Python's way to check for NaN
