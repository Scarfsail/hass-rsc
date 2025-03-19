from collections import deque
import datetime
import time
import logging

from ..entities.rsc_entity_type import RscEntityType

from .ios.abstract.rsc_io import RscIo

from .ios.rsc_aii import RscAii
from .ios.rsc_di import RscDi
from .ios.rsc_do import RscDo

from ..entities.rsc_entities_manager import RscEntitiesManager


class RscSlaveTelemetry:
    """Class for tracking telemetry data for an RSC slave device."""

    def __init__(
        self,
        entities_manager: RscEntitiesManager,
        telemetry_entities_id: str,
        slave_title: str,
        device_uid: str,
    ):
        """Initialize telemetry tracking for an RSC slave.
        Args:
            telemetry_entities_id: The ID of the telemetry entities
        """
        self._logger = logging.getLogger(__name__ + f" - Slave {telemetry_entities_id}")
        self._entities_manager = entities_manager
        self._telemetry_entities_id = telemetry_entities_id
        self._slave_title = slave_title
        self._device_uid = device_uid
        # Response time tracking
        self.response_times = deque(maxlen=50)  # Store last 50 measurements

        # Communication errors tracking
        self._comm_errors = deque(maxlen=100)  # Store timestamps of errors

        # Communication period tracking
        self._comm_period_timestamps = deque(
            maxlen=100
        )  # Store timestamps of get_data_for_slave calls
        self._last_comm_timestamp = (
            None  # Last timestamp when get_data_for_slave was called
        )

        # Last update timestamps for throttling
        self._last_response_time_update = 0
        self._last_comm_period_update = 0

        self._create_entities()

    def _create_entities(self):
        # Add average response time sensor
        self._average_response_time_io = RscAii(
            0, self._compose_entity_title("Průměrná doba odpovědi"), "ms"
        )
        self._average_response_time_io.is_online = True
        self._register_entity(
            RscEntityType.SENSOR,
            "response_time",
            self._average_response_time_io,
        )

        # Add online status binary sensor
        self.is_online_io = RscDi(0, self._compose_entity_title("Online"))
        self.is_online_io.is_online = True
        self._register_entity(
            RscEntityType.BINARY_SENSOR,
            "online",
            self.is_online_io,
            "connectivity",
        )

        # Add communication errors per minute sensor
        self._comm_errors_per_minute_io = RscAii(
            0, self._compose_entity_title("Chyby komunikace za minutu"), "errors/min"
        )
        self._comm_errors_per_minute_io.is_online = True
        self._register_entity(
            RscEntityType.SENSOR,
            "comm_errors_per_minute",
            self._comm_errors_per_minute_io,
        )

        # Add slave enable / disable switch
        self._slave_enabled_io = RscDo(
            0, self._compose_entity_title("Povolit komunikaci"), True
        )
        self._slave_enabled_io.is_online = True
        self._register_entity(
            RscEntityType.SWITCH, "slave_enabled", self._slave_enabled_io, "switch"
        )

        # Add communication period sensor
        self._comm_period_io = RscAii(
            0, self._compose_entity_title("Perioda komunikace"), "ms"
        )
        self._comm_period_io.is_online = True
        self._register_entity(
            RscEntityType.SENSOR,
            "comm_period",
            self._comm_period_io,
        )

        # Add slave enable / disable switch
        self.show_all_ios_as_attribute = RscDo(
            0, self._compose_entity_title("Zobrazit IOs jako atributy"), False
        )
        self.show_all_ios_as_attribute.is_online = True
        self._register_entity(
            RscEntityType.SWITCH,
            "show_all_ios_as_attribute",
            self.show_all_ios_as_attribute,
            "switch",
        )

    @property
    def slave_enabled(self):
        """Get the status of the slave enabled switch."""
        return self._slave_enabled_io.value

    def _register_entity(
        self,
        type: RscEntityType,
        entity_id: str,
        io: RscIo,
        device_class: str | None = None,
    ) -> None:
        self._entities_manager.register_entity_config(
            {
                "id": self._compose_entity_id(entity_id),
                "type": type.value,
                "title": io.title,
                "device_class": device_class,
                "unit": io.unit if hasattr(io, "unit") else None,
                "device_uid": self._device_uid,
                "entity_category": "diagnostic",
            },
            io,
        )

    def _compose_entity_id(self, entity_id: str) -> str:
        return f"rsc_device_{self._telemetry_entities_id}_{entity_id}"

    def _compose_entity_title(self, entity_title: str) -> str:
        return f"RSC Zařízení - {self._slave_title} - {entity_title}"

    def add_response_time(self, response_time_ms: float) -> None:
        """Add a response time measurement and update statistics.

        Args:
            response_time_ms: Response time in milliseconds
        """
        now = datetime.datetime.now()
        current_time = time.time()
        self.response_times.append((now, response_time_ms))

        # Remove measurements older than 5 seconds
        cutoff_time = now - datetime.timedelta(seconds=2)
        while self.response_times and self.response_times[0][0] < cutoff_time:
            self.response_times.popleft()

        # Calculate and update average if more than 1 second has passed since last update
        if current_time - self._last_response_time_update >= 1.0:
            if self.response_times:
                self._average_response_time_io.value = int(
                    sum(rt[1] for rt in self.response_times) / len(self.response_times)
                )
            else:
                self._average_response_time_io.value = 0

            self._last_response_time_update = current_time

        self.update_communication_error_rate()  # it needs to be also here to remove old errors when communication runs just fine and no errors are added

    def add_communication_error(self) -> None:
        """Record a communication error and update error rate statistics."""
        self._comm_errors.append(datetime.datetime.now())

        self.update_communication_error_rate()

    def update_communication_error_rate(self) -> None:
        # Remove errors older than 1 minute
        one_minute_ago = datetime.datetime.now() - datetime.timedelta(minutes=1)
        while self._comm_errors and self._comm_errors[0] < one_minute_ago:
            self._comm_errors.popleft()

        # Update the errors per minute sensor
        self._comm_errors_per_minute_io.value = len(self._comm_errors)

    def record_communication_timestamp(self) -> None:
        """Record a timestamp for communication period calculation."""
        now_timestamp = time.time()

        if self._last_comm_timestamp is not None:
            # Calculate period in milliseconds
            period_ms = (now_timestamp - self._last_comm_timestamp) * 1000
            self._comm_period_timestamps.append((now_timestamp, period_ms))

        # Always update the last timestamp
        self._last_comm_timestamp = now_timestamp

        # Calculate average period over the last 5 seconds
        # but always keep at least two measurements even if they're older
        cutoff_time = now_timestamp - 2.0  # 2 seconds

        # Make sure we keep at least 2 timestamps
        while (
            len(self._comm_period_timestamps) > 2
            and self._comm_period_timestamps[0][0] < cutoff_time
        ):
            self._comm_period_timestamps.popleft()

        # Calculate and update average if more than 1 second has passed since last update
        if now_timestamp - self._last_comm_period_update >= 1.0:
            if self._comm_period_timestamps:
                avg_period = sum(p[1] for p in self._comm_period_timestamps) / len(
                    self._comm_period_timestamps
                )
                self._comm_period_io.value = int(avg_period)
            else:
                self._comm_period_io.value = 0

            self._last_comm_period_update = now_timestamp
