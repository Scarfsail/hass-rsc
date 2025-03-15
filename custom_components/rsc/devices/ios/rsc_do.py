from .abstract.rsc_io_type import RscIoType
from .abstract.rsc_output import RscOutput


class RscDo(RscOutput):
    def __init__(self, io_index: int, title: str, default_value: bool = False):
        super().__init__(io_index, title, default_value)

    def get_io_type_id(self) -> RscIoType:
        return RscIoType.DO

    def get_io_data_length(self) -> int:
        return 1

    def append_value(self, data: bytearray, position: int) -> None:
        data[position] = 1 if self.value else 0
