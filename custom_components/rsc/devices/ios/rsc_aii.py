from .abstract.rsc_io_type import RscIoType
from .rsc_ai import RscAi


class RscAii(RscAi):
    def __init__(self, io_index: int, title: str, units: str, default_value: int = 0):
        super().__init__(io_index, title, units, default_value)

    def get_io_type_id(self) -> RscIoType:
        return RscIoType.AII

    def get_io_data_length(self) -> int:
        return 4

    def _process_value(self, data: bytes, position: int) -> int:
        return (
            data[position]
            | (data[position + 1] << 8)
            | (data[position + 2] << 16)
            | (data[position + 3] << 24)
        )
