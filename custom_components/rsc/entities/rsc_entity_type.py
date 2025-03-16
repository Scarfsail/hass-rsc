from enum import StrEnum


class RscEntityType(StrEnum):
    SENSOR = "sensor"
    BINARY_SENSOR = "binary_sensor"
    BUTTON = "button"
    SWITCH = "switch"
    GATE = "gate"
    NUMBER = "number"
    LIGHT = "light"
