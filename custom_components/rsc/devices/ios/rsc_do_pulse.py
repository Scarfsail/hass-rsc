from .rsc_do import RscDo


class RscDoPulse(RscDo):
    def __init__(self, io_index: int, title: str, default_value: bool = False):
        super().__init__(io_index, title, default_value)

    @property
    def is_pulse_output(self) -> bool:
        return True

    @property
    def pulse_reset_value(self):
        return False
