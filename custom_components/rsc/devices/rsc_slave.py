import datetime
import logging
from typing import Any, Literal

from ..entities.rsc_entities_manager import RscEntitiesManager

from .ios.abstract.rsc_input import RscInput
from .ios.abstract.rsc_output import RscOutput
from .ios.rsc_io_factory import create_rsc_input, create_rsc_output


class RscSlave:
    """Class representing an RSC slave device."""

    # Constants
    RSC_COMMAND_SEND_ME_ALL_IO = 1

    RSC_DATA_TYPE_INPUTS = 1
    RSC_DATA_TYPE_OUTPUTS = 2

    def __init__(
        self,
        slave_id: int,
        title: str,
        ios_config: dict[str, Any],
        entities_manager: RscEntitiesManager,
    ):
        """Initialize RscSlave with ID, title, and I/O configuration."""
        self._logger = logging.getLogger(__name__ + f" - Slave {slave_id}")

        self.slave_id = slave_id
        self.title = title
        self._entities_manager = entities_manager

        self.inputs: list[RscInput] = self._create_ios(ios_config, "inputs")
        self.outputs: list[RscOutput] = self._create_ios(ios_config, "outputs")

        self.last_processed_incoming_data: datetime = None
        self.last_received_valid_data: datetime = None
        self.last_sent_data: datetime = None
        self._is_online = False
        self.last_online: datetime = None

        self._logger.info(
            f"Initialized slave: {title} (ID: {slave_id}) "
            f"with {len(self.inputs)} inputs and {len(self.outputs)} outputs"
        )
        self.packet_id = 1  # Add packet_id attribute
        self.all_outputs_requested = False  # Add all_outputs_requested attribute

    def get_data_for_slave(self) -> bytes:
        """Return data to be sent to the slave.

        Returns:
            Byte array containing the formatted data for the slave
        """
        self.last_sent_data = datetime.datetime.now()

        data = bytearray(255)  # Initialize with max size
        position_in_buff = 0

        # PACKET ID (1 byte)
        data[position_in_buff] = self.packet_id
        position_in_buff += 1

        # COMMANDS (1 byte)
        command = 0
        # When slave isn't online, request all inputs
        if not self._is_online:
            command |= self.RSC_COMMAND_SEND_ME_ALL_IO
        data[position_in_buff] = command
        position_in_buff += 1

        # OUTPUTS section
        data[position_in_buff] = self.RSC_DATA_TYPE_OUTPUTS
        position_in_buff += 1

        # Save position for output count, will be filled later
        outputs_count_buff_position = position_in_buff
        position_in_buff += 1
        outputs_count = 0

        # Output processing would go here, similar to C# commented code
        if self.outputs:
            for output in self.outputs:
                result = output.append_to_outcoming_data(
                    self.packet_id,
                    data,
                    position_in_buff,
                    self.all_outputs_requested,
                )
                if result[0]:
                    outputs_count += 1
                    position_in_buff = result[1]

        # Set the actual count of outputs
        data[outputs_count_buff_position] = outputs_count

        # Trim the response to actual size
        data_for_slave = bytes(data[:position_in_buff])

        return data_for_slave

    @property
    def is_online(self) -> bool:
        return self._is_online

    def set_is_online(self, is_online: bool):
        """Set the online status of the slave."""
        if is_online == self._is_online:
            return

        self._is_online = is_online
        if is_online:
            for output in self.outputs:
                output.is_online = True
            self._logger.info(f"Slave {self.slave_id} is online")
        else:
            self.all_outputs_requested = True
            for output in self.outputs:
                output.is_online = False
            for inp in self.inputs:
                inp.is_online = False
            self._logger.info(f"Slave {self.slave_id} is offline")

    def process_incoming_data(self, data: bytes):
        """Process incoming data from the slave."""
        self.last_processed_incoming_data = datetime.datetime.now()

        if not data:
            self.check_if_is_still_online()
            return

        try:
            #  ********* DATA Structure    ***********
            #    1B    |     1B    |   1B      |   X  | 1B       |  X   | ...
            # PacketId |  Command  |  DataType | Data | DataType | Data | ...
            #
            position_in_buff = 0

            # Get packet ID
            received_packet_id = data[position_in_buff]
            position_in_buff += 1

            # Get command
            received_command = data[position_in_buff]
            position_in_buff += 1
            self.all_outputs_requested = (
                received_command & self.RSC_COMMAND_SEND_ME_ALL_IO
            ) == self.RSC_COMMAND_SEND_ME_ALL_IO

            # Process incoming data (inputs, etc.)
            while position_in_buff < len(data):
                received_data_type = data[position_in_buff]
                position_in_buff += 1

                if received_data_type == self.RSC_DATA_TYPE_INPUTS:
                    result = self._process_incoming_inputs(data, position_in_buff)
                    position_in_buff = (
                        result[1] if result[0] else len(data)
                    )  # Finish processing
                else:
                    self._logger.debug(
                        f"Not recognized type of data: {received_data_type}"
                    )
                    position_in_buff = len(data)  # Finish processing

            if (
                received_packet_id != 0
            ):  # When received_packet_id == 0, the slave device sent data asynchronously
                if not self.outputs:
                    raise Exception("outputs can't be None when processing inputs.")

                self.packet_id = received_packet_id
                # Increment packet ID for next request, ensuring it's never 0
                self.packet_id += 1
                if self.packet_id > 255:
                    self.packet_id = 1

                # Notify all outputs that response was received
                for output in self.outputs:
                    output.response_received_from_slave(received_packet_id)

            self.set_is_online(True)
            self._set_last_online(datetime.datetime.now())

            self.last_received_valid_data = datetime.datetime.now()

        except Exception as ex:
            self._logger.error(
                f"Error while processing data from slave {self.slave_id}: {str(ex)}"
            )
            self.check_if_is_still_online()

    def _process_incoming_inputs(self, data: bytes, position_in_buff: int) -> bool:
        """Process incoming inputs data.

        Args:
            data: The received data
            position_in_buff: Current position in buffer

        Returns:
            True if processing was successful, False otherwise
        """
        #  ********* DATA Structure    ***********
        #    1B         |   X  |
        #   Count of IO | IOs  |
        #
        if not self.inputs:
            raise Exception("inputs can't be None when processing inputs.")

        io_count = data[position_in_buff]
        position_in_buff += 1
        processed_ios = 0

        while io_count > processed_ios:
            io_idx = data[position_in_buff]  # Get the Input's index from the buffer

            if io_idx > len(self.inputs) - 1:
                self._logger.error(
                    f"Received IO INPUT index: {io_idx} which is higher than amount of Inputs in this system: {len(self.inputs)}"
                )
                return False

            result = self.inputs[io_idx].process_incoming_data(data, position_in_buff)
            if not result[0]:
                return False

            position_in_buff = result[1]
            processed_ios += 1

        return (True, position_in_buff)

    def check_if_is_still_online(self):
        """Check if the slave is still online based on timing."""
        if not self._is_online:
            return

        # Check if valid data wasn't received within last 4 seconds
        now = datetime.datetime.now()
        timeout = datetime.timedelta(seconds=4)
        if (
            self.last_received_valid_data
            and now >= self.last_received_valid_data + timeout
        ):
            self._logger.error(
                f"Valid data from RSC Slave {self.slave_id}, {self.title} weren't received within {timeout.total_seconds()} seconds. Last valid data was received {self.last_received_valid_data}. Setting the slave to offline."
            )
            self.set_is_online(False)

    def _set_last_online(self, time: datetime.datetime):
        """Set the last time the slave was seen online."""
        # Implementation to track last online time
        self.last_online = time

    def _create_ios(
        self, ios_config: dict[str, Any], io_type: Literal["inputs", "outputs"]
    ) -> list[RscInput | RscOutput]:
        ios = []

        if io_type not in ios_config:
            self._logger.warning(f"No {io_type} defined in configuration")
            return ios

        for io_config in ios_config[io_type]:
            if io_type == "inputs":
                io_obj = create_rsc_input(io_config)
            else:  # outputs
                io_obj = create_rsc_output(io_config)
            ios.append(io_obj)
            self._logger.debug(
                f"Created {io_type[:-1]}: {io_obj.title} (ID: {io_obj.io_index})"
            )

            # Entities
            entities = io_config.get("entities")
            if entities:
                for entity_config in entities:
                    # Merge IO config with entity config without creating new objects
                    merged_config = {**io_config, **entity_config}
                    self._entities_manager.register_entity_config(merged_config, io_obj)

        # Validate I/O indices - must start at 0, have no gaps, and no duplicates
        io_indices = [io.io_index for io in ios]
        if not io_indices:
            return ios

        # Check if starts with 0
        if min(io_indices) != 0:
            self._logger.error(
                f"{io_type} indices must start at 0, found {min(io_indices)}"
            )
            raise ValueError(f"{io_type} indices must start at 0")

        # Check for gaps and duplicates
        expected_indices = set(range(max(io_indices) + 1))
        if len(io_indices) != len(expected_indices):
            duplicates = [idx for idx in io_indices if io_indices.count(idx) > 1]
            if duplicates:
                self._logger.error(f"Duplicate {io_type} indices found: {duplicates}")
                raise ValueError(f"Duplicate {io_type} indices found: {duplicates}")
            else:
                missing = expected_indices - set(io_indices)
                self._logger.error(f"Gaps in {io_type} indices found: {missing}")
                raise ValueError(f"Missing {io_type} indices: {missing}")

        self._logger.info(f"Created {len(ios)} {io_type} for slave {self.slave_id}")
        return ios
