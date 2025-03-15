from .abstract.rsc_io_type import RscIoType
from .abstract.rsc_output import RscOutput


class RscAoi(RscOutput):
    def __init__(
        self, io_index: int, title: str, units: str = "", default_value: int = 0
    ):
        super().__init__(io_index, title, default_value)
        self._units = units

    def get_io_type_id(self) -> RscIoType:
        return RscIoType.AOI

    def get_io_data_length(self) -> int:
        return 4

    def append_value(self, data: bytearray, position: int) -> None:
        data[position] = self.value & 0xFF
        data[position + 1] = (self.value >> 8) & 0xFF
        data[position + 2] = (self.value >> 16) & 0xFF
        data[position + 3] = (self.value >> 24) & 0xFF

    @property
    def units(self) -> str:
        return self._units
