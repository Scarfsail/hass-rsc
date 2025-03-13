import datetime
import logging
from typing import Any


class RscSlave:
    """Class representing an RSC slave device."""

    # Constants
    RSC_COMMAND_SEND_ME_ALL_IO = 1
    RSC_DATA_TYPE_OUTPUTS = 1  # Added this constant based on C# code

    def __init__(self, slave_id: int, title: str, ios_config: dict[str, Any]):
        """Initialize RscSlave with ID, title, and I/O configuration."""
        self.slave_id = slave_id
        self.title = title
        self.inputs = ios_config.get("inputs", [])
        self.outputs = ios_config.get("outputs", [])

        self.last_processed_incoming_data: datetime = None
        self.last_sent_data: datetime = None
        self.is_online = False

        self._logger = logging.getLogger(__name__ + f" - Slave {slave_id}")
        self._logger.info(
            f"Initialized slave: {title} (ID: {slave_id}) "
            f"with {len(self.inputs)} inputs and {len(self.outputs)} outputs"
        )
        self.packet_id = 0  # Add packet_id attribute
        self.all_outputs_requested = False  # Add all_outputs_requested attribute

    def get_data_for_slave(self) -> bytes:
        """Return data to be sent to the slave.

        Returns:
            Byte array containing the formatted data for the slave
        """
        self.last_sent_data = datetime.datetime.now()

        response_data = bytearray(255)  # Initialize with max size
        position_in_buff = 0

        # PACKET ID (1 byte)
        response_data[position_in_buff] = self.packet_id
        position_in_buff += 1

        # COMMANDS (1 byte)
        command = 0
        # When slave isn't online, request all inputs
        if not self.is_online:
            command |= self.RSC_COMMAND_SEND_ME_ALL_IO
        response_data[position_in_buff] = command
        position_in_buff += 1

        # OUTPUTS section
        response_data[position_in_buff] = self.RSC_DATA_TYPE_OUTPUTS
        position_in_buff += 1

        # Save position for output count, will be filled later
        outputs_count_buff_position = position_in_buff
        position_in_buff += 1
        outputs_count = 0

        # Output processing would go here, similar to C# commented code
        # if not outputs_suspended and self.outputs:
        #     for output in self.outputs:
        #         if output.append_to_outcoming_data(self.packet_id, response_data, position_in_buff, self.all_outputs_requested):
        #             outputs_count += 1
        #             # position_in_buff would be updated by the method

        # Set the actual count of outputs
        response_data[outputs_count_buff_position] = outputs_count

        # Trim the response to actual size
        data_for_slave = bytes(response_data[:position_in_buff])

        return data_for_slave

    def process_incoming_data(self, data: bytes):
        """Process incoming data from the master."""
        self.last_processed_incoming_data = datetime.datetime.now()
        self._logger.debug(f"Processing incoming data: {len(data)} bytes")
        self.is_online = True
        # Process the data and update the input values
