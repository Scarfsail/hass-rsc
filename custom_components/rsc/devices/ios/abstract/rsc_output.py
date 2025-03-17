from abc import ABC, abstractmethod
import logging
import threading

from .rsc_io import RscIo

_LOGGER = logging.getLogger(__name__)


class RscOutput(RscIo, ABC):
    """Base class for RSC output implementations."""

    PACKET_ID_VALUE_CHANGED = -1
    PACKET_ID_VALUE_RECEIVED = -2

    def __init__(self, io_index: int, title: str, default_value):
        """Initialize the RSC output."""
        super().__init__(io_index, title, default_value)
        self._changed_value_sent_with_packet_id = 0
        self._packet_id_lock = threading.RLock()  # Added lock for thread safety
        self.persist_value_and_last_change = False

    @abstractmethod
    def append_value(self, data: bytearray, position: int) -> None:
        """Append the value to the outgoing data array.

        Args:
            data: Array of bytes
            position: Position in array to start writing to
        """

    def append_to_outcoming_data(
        self, packet_id: int, data: bytearray, position: int, force_send: bool
    ) -> tuple[bool, int]:
        """Append output data to the outgoing data array.

        Args:
            packet_id: ID of the packet
            data: Array of bytes
            position: Position in array to start writing to
            force_send: Whether to force sending the data

        Returns:
            tuple: (success, new position)
        """
        if force_send or (
            self._changed_value_sent_with_packet_id != self.PACKET_ID_VALUE_RECEIVED
        ):
            with self._packet_id_lock:  # Use lock when modifying packet ID
                self._changed_value_sent_with_packet_id = packet_id

                data[position] = self.io_index
                position += 1
                data[position] = self.get_io_type_id()
                position += 1

                self.append_value(data, position)
                position += self.get_io_data_length()

            return True, position

        return False, position

    def response_received_from_slave(self, packet_id: int) -> None:
        """Handle response received from slave.

        Args:
            packet_id: ID of the packet
        """
        with self._packet_id_lock:  # Use lock when checking/modifying packet ID
            if packet_id == self._changed_value_sent_with_packet_id:
                self._changed_value_sent_with_packet_id = self.PACKET_ID_VALUE_RECEIVED
                self._on_response_received_from_slave()

    def _on_response_received_from_slave(self) -> None:
        """Handle response from slave device."""
        if self.is_pulse_output:
            self.value = self.pulse_reset_value

    def _on_is_online_change(self) -> None:
        """Handle changes to the online status."""
        super()._on_is_online_change()
        if self.is_pulse_output:
            self.value = self.pulse_reset_value

    @property
    def pulse_reset_value(self):
        """Get the reset value for pulse outputs."""
        return None

    @property
    def is_pulse_output(self) -> bool:
        """Determine if this is a pulse output."""
        return False

    def write(self, value) -> bool:
        """Write a value to the output.

        Args:
            value: The value to write

        Returns:
            True if successful, False otherwise
        """
        self.value = value
        return True

    def _on_changed(self) -> None:
        """Handle value changes."""
        with self._packet_id_lock:  # Use lock when modifying packet ID
            self._changed_value_sent_with_packet_id = self.PACKET_ID_VALUE_CHANGED

        super()._on_changed()

    @property
    def is_output(self) -> bool:
        """Indicate if this is an output."""
        return True
