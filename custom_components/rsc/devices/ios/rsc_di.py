from .abstract.rsc_io_type import RscIoType
from .abstract.rsc_input import RscInput


class RscDi(RscInput):
    def __init__(self, io_index: int, title: str, default_value: bool = False):
        super().__init__(io_index, title, default_value)

    def get_io_type_id(self) -> RscIoType:
        return RscIoType.DI

    def get_io_data_length(self) -> int:
        return 1

    def _process_value(self, data: bytes, position: int) -> bool:
        return data[position] == 1
