from enum import IntEnum


class RscIoType(IntEnum):
    """I/O type enumeration."""

    DI = 1  # Digital Input
    DO = 2  # Digital Output
    AII = 3  # Analog Input Integer
    AIF = 4  # Analog Input Float
    AOB = 5  # Analog Output Binary
    AIB = 6  # Analog Input Binary
    AOI = 7  # Analog Output Integer
    AOF = 8  # Analog Output Float
    SI = 9  # Status Input
    JI = 10  # JSON Input
