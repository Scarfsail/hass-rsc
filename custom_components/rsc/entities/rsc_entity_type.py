from enum import StrEnum


class RscEntityType(StrEnum):
    SENSOR = "sensor"
    BINARY_SENSOR = "binary_sensor"
    BUTTON = "button"
    SWITCH = "switch"
    COVER = "cover"
    NUMBER = "number"
