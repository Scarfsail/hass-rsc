from collections import deque
import datetime
import logging

from ..entities.rsc_entity_type import RscEntityType

from .ios.abstract.rsc_io import RscIo

from .ios.rsc_aii import RscAii
from .ios.rsc_di import RscDi

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

        self._create_entities()

    def _create_entities(self):
        self._average_response_time_io = RscAii(
            0, self._compose_entity_title("Průměrná doba odpovědi"), "ms"
        )
        self._average_response_time_io.is_online = True
        self._register_entity(
            RscEntityType.SENSOR,
            "response_time",
            self._average_response_time_io,
        )

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

    def _register_entity(
        self, type: RscEntityType, entity_id: str, io: RscIo, device_class: str = None
    ) -> None:
        self._entities_manager.register_entity_config(
            {
                "id": self._compose_entity_id(entity_id),
                "type": type.value,
                "title": io.title,
                "device_class": device_class,
                "unit": io.unit if hasattr(io, "unit") else None,
                "device_uid": self._device_uid,
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
        self.response_times.append((now, response_time_ms))

        # Remove measurements older than 5 seconds
        cutoff_time = now - datetime.timedelta(seconds=5)
        while self.response_times and self.response_times[0][0] < cutoff_time:
            self.response_times.popleft()

        # Calculate new average if there are measurements
        if self.response_times:
            self._average_response_time_io.value = int(
                sum(rt[1] for rt in self.response_times) / len(self.response_times)
            )
        else:
            self._average_response_time_io.value = 0

        self._update_communication_error_rate()

    def add_communication_error(self) -> None:
        """Record a communication error and update error rate statistics."""
        now = datetime.datetime.now()
        self._comm_errors.append(now)

        # Remove errors older than 1 minute
        one_minute_ago = now - datetime.timedelta(minutes=1)
        while self._comm_errors and self._comm_errors[0] < one_minute_ago:
            self._comm_errors.popleft()
        self._update_communication_error_rate()

    def _update_communication_error_rate(self) -> None:
        # Update the errors per minute sensor
        self._comm_errors_per_minute_io.value = len(self._comm_errors)
