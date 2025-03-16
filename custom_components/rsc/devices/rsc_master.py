import datetime
import threading
import time
import logging
from typing import Dict, Optional, Any, List
from urllib import response

from numpy import byte
from .rsc_serial import RscSerial
from .rsc_slave import RscSlave


class RscMaster:
    def __init__(self, port: str, title: str, slaves: list[RscSlave]):
        """Initialize RscMaster with serial port configuration."""
        self.port = port
        self.title = title
        self.slaves = slaves

        self.serial: RscSerial = None
        self.communication_thread: threading.Thread = None
        self.running = False
        self._logger = logging.getLogger(__name__ + " - " + port)

    def begin_communication(self):
        """Open the serial port and start the communication thread."""
        try:
            self.serial = RscSerial(port=self.port)

            if self.serial.open():
                self._logger.info(f"Successfully opened serial port {self.port}")
                self.running = True
                self.communication_thread = threading.Thread(
                    target=self._communication_loop
                )
                self.communication_thread.daemon = True
                self.communication_thread.start()
                return True

            self._logger.error(f"Failed to open serial port {self.port}")
            return False

        except Exception as e:
            self._logger.error(f"Serial communication error: {e}")
            return False

    def _communication_loop(self):
        """Thread function that manages communication with slaves."""
        current_slave_index = 0

        while (
            self.running
            and self.serial
            and self.serial.serial
            and self.serial.serial.is_open
        ):
            try:
                # No slaves to communicate with
                if not self.slaves:
                    time.sleep(1)
                    continue

                # Get current slave to communicate with
                slave = self.slaves[current_slave_index]

                # Skip communication if last attempt was less than 5 seconds ago
                if (
                    not slave.is_online
                    and slave.last_sent_data is not None
                    and slave.last_sent_data
                    > (datetime.datetime.now() - datetime.timedelta(seconds=5))
                ):
                    continue

                # Get data to send to the slave
                data_to_send = slave.get_data_for_slave()
                if data_to_send:
                    response_data = self.send_data_and_receive_response(
                        slave.slave_id, data_to_send
                    )
                    if response_data:
                        # Forward the response to the slave for processing
                        slave.process_incoming_data(response_data)
                    else:
                        slave.check_if_is_still_online()
                        self._logger.debug(
                            f"No response received from slave {slave.slave_id}"
                        )
                    time.sleep(50 / 1000)  # Small delay to avoid flooding the bus
                else:
                    self._logger.debug(f"No data to send to slave {slave.slave_id}")

            except Exception as e:
                slave.is_online = False
                self._logger.error(f"Error in communication loop: {e}")
            finally:
                # Move to the next slave
                current_slave_index = (current_slave_index + 1) % len(self.slaves)

    def send_data_and_receive_response(self, slave_address: byte, data: bytes) -> bytes:
        """Send data to the slave and receive the response."""
        packet_to_send = self.create_packet_from_data(slave_address, data)
        self.serial.write(packet_to_send)
        self._logger.debug(
            f"Sent to slave {slave_address}: {len(packet_to_send)} bytes"
        )

        response_packet = self.serial.read(slave_address)
        if response_packet:
            self._logger.debug(
                f"Received from slave {slave_address}: {len(response_packet)} bytes"
            )
            response_data = self.get_data_from_received_packet(
                response_packet, slave_address
            )
            return response_data
        return b""

    def create_packet_from_data(self, slave_address: int, data: bytes) -> bytes:
        """Create a packet from data with the specified format.

        Packet format:
        | 1B PacketLen | 1B Addr | X Data | 1B CRC |
        Master has always address 0

        Args:
            slave_address: Address of the slave
            data: Data to be included in the packet

        Returns:
            Complete packet as bytes

        Raises:
            ValueError: If data is too long
        """
        if len(data) > 255 - 3:
            raise ValueError(
                f"Slave: {slave_address} Data can't be longer than 255-3 bytes"
            )

        # Create packet: length byte + address byte + data + CRC byte
        packet = bytearray(1 + 1 + len(data) + 1)
        packet[0] = len(data) + 3  # Total packet length
        packet[1] = slave_address

        # Copy data into packet
        for i, b in enumerate(data):
            packet[i + 2] = b

        # Calculate and add CRC
        crc = self.calculate_crc(packet, len(packet))
        packet[-1] = crc

        return bytes(packet)

    def calculate_crc(self, packet_with_crc_in_last_byte: bytes, length: int) -> int:
        """Calculate CRC by summing all bytes except the last one.

        Args:
            packet_with_crc_in_last_byte: Packet data with space for CRC in last byte
            length: Length of the packet

        Returns:
            Calculated CRC value
        """
        crc = 0
        for i in range(length - 1):
            crc += packet_with_crc_in_last_byte[i]

        # Ensure the CRC is a byte (0-255)
        return crc & 0xFF

    def get_data_from_received_packet(
        self, received_packet: bytes, slave_address: int
    ) -> bytes:
        """Extract and validate data from a received packet.

        Args:
            received_packet: The complete packet received
            slave_address: Expected slave address to validate against

        Returns:
            The extracted data portion of the packet or empty bytes if validation fails
        """
        if not received_packet:
            self._logger.error(f"Slave: {slave_address} sent empty message")
            return b""

        # Get packet size from first byte
        packet_size = received_packet[0] if received_packet else 0

        # Validate minimum packet size (length byte + address byte + at least 1 data byte + CRC byte)
        if len(received_packet) == 0 or packet_size < 4:
            self._logger.error(
                f"Slave: {slave_address} sent wrong message - packetSize: {packet_size}, "
                f"input buffer length: {len(received_packet)}. Data: {received_packet.hex(' ')}"
            )
            return b""

        # Validate slave address
        received_slave_address = received_packet[1]
        if received_slave_address != slave_address:
            self._logger.error(
                f"Slave: {slave_address} wrong slave address. Required: {slave_address} "
                f"Received: {received_slave_address}"
            )
            return b""

        # Validate CRC
        crc = self.calculate_crc(received_packet, packet_size)
        received_crc = received_packet[packet_size - 1]
        if crc != received_crc:
            self._logger.error(
                f"Slave: {slave_address} wrong CRC. Calculated: {crc} Received: {received_crc}"
            )
            return b""

        # Extract data portion (between address byte and CRC byte)
        received_data = received_packet[2 : packet_size - 1]

        return received_data

    def stop_communication(self):
        """Stop the communication thread and close the serial port."""
        self.running = False
        if self.communication_thread:
            self.communication_thread.join(timeout=2.0)
            self.communication_thread = None

        if self.serial:
            self.serial.close()
            self._logger.info("Serial port closed")
            return True
        return False
