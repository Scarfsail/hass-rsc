from abc import ABC, abstractmethod
import datetime
import logging

from .rsc_io import RscIo

_LOGGER = logging.getLogger(__name__)


class RscInput(RscIo, ABC):
    """Base class for RSC input implementations."""

    def __init__(self, io_index: int, title: str, default_value):
        """Initialize the RSC input."""
        super().__init__(io_index, title, default_value)
        self.last_received_valid_data = None
        self.persist_value_and_last_change = True

    def process_incoming_data(self, data: bytes, position: int) -> tuple[bool, int]:
        """Process incoming data and update the value.

        Args:
            data: Array of bytes
            position: Position in array to start reading from

        Returns:
            tuple: (success, new position)
        """
        received_idx = data[position]
        position += 1

        if received_idx != self.io_index:
            _LOGGER.error(
                f"Index: {received_idx} is not index of this IO {self.io_index}"
            )
            return False, position

        received_io_type_id = data[position]
        position += 1

        if received_io_type_id != self.get_io_type_id():
            _LOGGER.error(
                f"typeID: {received_io_type_id} is not type id of this IO: {self.get_io_type_id()}"
            )
            return False, position

        data_length = self.get_io_data_length()
        input_is_online = not self._data_contains_offline_flag(
            data, position, data_length
        )

        if input_is_online:
            received_value = self._process_value(data, position)
            self.value = received_value
            input_is_online = self._is_processed_value_valid(received_value)
            if input_is_online:
                self.last_received_valid_data = datetime.datetime.now()

        self.is_online = input_is_online
        position += data_length

        return True, position

    @abstractmethod
    def _process_value(self, data: bytes, position: int):
        """Process raw data into a value of type T.

        Args:
            data: Array of bytes
            position: Position in array to start reading from

        Returns:
            Processed value of type T
        """

    def _is_processed_value_valid(self, value) -> bool:
        """Check if the processed value is valid.

        Args:
            value: The processed value

        Returns:
            True if the value is valid, False otherwise
        """
        return True

    def _data_contains_offline_flag(
        self, data: bytes, offset: int, data_length: int
    ) -> bool:
        """Returns true when all bytes from offset to data_length are equal to 0xFF (255).
        It means the Input is offline and doesn't contain real data.

        Args:
            data: Array of bytes
            offset: Position to start checking from
            data_length: Number of bytes to check

        Returns:
            True if the data contains the offline flag, False otherwise
        """

        return all(data[offset + i] == 255 for i in range(data_length))
