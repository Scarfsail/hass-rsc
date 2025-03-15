from abc import ABC
import logging

from .abstract.rsc_input import RscInput

_LOGGER = logging.getLogger(__name__)


class RscAi(RscInput, ABC):
    """Base class for RSC analog input implementations."""

    def __init__(self, io_index: int, title: str, units: str, default_value):
        """Initialize the RSC analog input.

        Args:
            io_index: The index of this I/O
            title: The title or name of this I/O
            units: The measurement units of this input
            default_value: The default value for this input
        """
        super().__init__(io_index, title, default_value)
        self._units = units

    @property
    def units(self) -> str:
        """Get the measurement units of this analog input.

        Returns:
            The units string
        """
        return self._units
