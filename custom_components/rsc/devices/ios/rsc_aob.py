from .abstract.rsc_io_type import RscIoType
from .abstract.rsc_output import RscOutput


class RscAob(RscOutput):
    def __init__(
        self, io_index: int, title: str, units: str = "", default_value: int = 0
    ):
        super().__init__(io_index, title, default_value)
        self._units = units

    def get_io_type_id(self) -> RscIoType:
        return RscIoType.AOB

    def get_io_data_length(self) -> int:
        return 1

    def append_value(self, data: bytearray, position: int) -> None:
        data[position] = int(self.value) & 0xFF  # Ensure it's in byte range (0-255)

    @property
    def units(self) -> str:
        return self._units
