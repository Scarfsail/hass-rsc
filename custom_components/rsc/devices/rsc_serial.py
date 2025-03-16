import serial
import time
import logging

_LOGGER = logging.getLogger(__name__)


class RscSerial:
    def __init__(
        self, port: str, response_timeout_ms: int = 1000, input_buffer_size: int = 1024
    ):
        """Initialize RscSerial with serial port configuration.

        Args:
            port: Serial port name
            response_timeout_ms: Timeout for responses in milliseconds
            input_buffer_size: Size of input buffer
        """
        self.port_name = port
        self.baudrate = 57600  # Hardcoded as requested
        self.response_timeout_ms = response_timeout_ms
        self.input_buffer_size = input_buffer_size
        self.serial: serial.Serial = None
        self.stop_communication = False

    def open(self):
        """Open the serial port."""
        if self.serial and self.serial.is_open:
            return True

        _LOGGER.info(f"Opening serial port {self.port_name} ...")
        self.stop_communication = False

        try:
            self.serial = serial.Serial(
                port=self.port_name,
                baudrate=self.baudrate,
                timeout=self.response_timeout_ms / 1000,  # Convert ms to seconds
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
            )
            self.serial.rts = False
        except Exception as ex:
            if self.serial:
                self.serial.close()
                self.serial = None
            error_msg = f"Error while opening COM port: {self.port_name}. {str(ex)}"
            _LOGGER.error(error_msg)
            return False

        _LOGGER.info(f"Serial port {self.port_name} is opened.")
        return True

    def open_comm_and_repeat_until_successful(self):
        """Try to open the port and repeat until successful."""
        while not self.stop_communication and not self.open():
            _LOGGER.error(
                f"Com port: {self.port_name} is not opened, waiting 5 seconds to try open it again..."
            )
            time.sleep(5)
        return self.serial and self.serial.is_open

    def close(self):
        """Close the serial port."""
        _LOGGER.info("Closing serial port.")
        self.stop_communication = True
        if self.serial:
            self.serial.close()

    def write(self, buffer):
        """Write data to the port with RTS control.

        Args:
            buffer: Bytes to write

        Returns:
            int: Number of bytes written
        """
        try:
            if not self.serial or len(buffer) == 0:
                return 0

            self.serial.reset_input_buffer()
            self.serial.flush()

            # Perform the physical write on the RS485 bus
            # Set Transmit
            self.serial.rts = True

            bytes_written = self.serial.write(buffer)

            # Set receive
            self.serial.rts = False

            return bytes_written

        except Exception as ex:
            _LOGGER.error(f"Error while writing data ({len(buffer)} bytes): {str(ex)}")
            _LOGGER.info("Closing serial port to restart it...")
            if self.serial:
                self.serial.close()
            time.sleep(0.5)
            _LOGGER.info("Opening serial port to restart it...")
            if self.serial:
                self.serial.open()
            _LOGGER.info(
                "Serial port has been re-initialized, re-throwing the exception"
            )
            raise

    def read(self, slave_address):
        """Read data from the port.

        Args:
            slave_address: Byte address of the slave device

        Returns:
            bytes: Data read from the port
        """
        try:
            if not self.serial:
                return b""

            input_buffer = bytearray()
            packet_size = 255

            # Wait for response
            start_time = time.time()

            while len(input_buffer) < packet_size:
                waiting_bytes = self.serial.in_waiting
                received_buffer = self.serial.read(
                    waiting_bytes if waiting_bytes > 0 else 1
                )

                if len(received_buffer) > 0 and packet_size == 255:
                    packet_size = received_buffer[0]

                input_buffer.extend(received_buffer)

                if len(input_buffer) < packet_size:
                    # Check if we've exceeded timeout
                    elapsed = (time.time() - start_time) * 1000
                    if elapsed > self.response_timeout_ms:
                        if len(input_buffer) == 0:
                            _LOGGER.info(
                                f"Response for slave: {slave_address} wasn't received in given time: {self.response_timeout_ms} ms."
                            )
                        else:
                            _LOGGER.info(
                                f"Response wasn't fully received for slave: {slave_address}. Received bytes: {len(input_buffer)}, expected packet size: {packet_size}"
                            )
                        return b""
                    time.sleep(20 / 1000)
                    continue
            return bytes(input_buffer)

        except Exception as ex:
            _LOGGER.error(f"Error reading data: {str(ex)}")
            return b""

    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
