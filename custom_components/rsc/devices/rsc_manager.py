import logging
import os
from pathlib import Path

import yaml

from homeassistant.helpers.device_registry import DeviceRegistry

from .. import const
from ..entities.rsc_entities_manager import RscEntitiesManager
from .rsc_master import RscMaster
from .rsc_slave import RscSlave


class RscManager:
    """Class to manage RSC masters and slaves from configuration."""

    def __init__(
        self,
        config_path: Path,
        entities_manager: RscEntitiesManager,
        device_registry: DeviceRegistry,
        config_entry_id: str,
    ):
        """Initialize the RSC manager with config file path."""
        self.config_path = config_path
        self._entities_manager = entities_manager
        self._device_registry = device_registry
        self._config_entry_id = config_entry_id
        self._masters: dict[str, RscMaster] = {}
        self._logger = logging.getLogger(__name__)

    def load_config(self) -> bool:
        """Load configuration from YAML file."""
        try:
            if not os.path.exists(self.config_path):
                self._logger.error(f"Config file not found: {self.config_path}")
                return False

            with open(self.config_path, "r") as file:
                config = yaml.safe_load(file)

            if not config or "masters" not in config:
                self._logger.error("Invalid configuration: 'masters' section missing")
                return False

            shared_communication_config = config.get("communication_config", {})

            # Create masters from config
            for master_config in config["masters"]:
                communication_config = {
                    **shared_communication_config,
                    **master_config.get("communication_config", {}),
                }

                if "port" not in communication_config:
                    self._logger.error(
                        f"Invalid communication_config config: {communication_config}"
                    )
                    continue
                if "title" not in master_config:
                    self._logger.error(f"Invalid master config: {master_config}")

                port = communication_config["port"]
                title = master_config["title"]
                slaves_config = master_config.get("slaves", [])

                # Process slaves for this master
                slaves = []  # Changed from dictionary to list
                for slave_config in slaves_config:
                    if "id" not in slave_config or "title" not in slave_config:
                        self._logger.error(f"Invalid slave config: {slave_config}")
                        continue

                    slave_id = slave_config["id"]
                    slave_telemetry_entities_id = slave_config.get(
                        "telemetry_entities_id", str(slave_id)
                    )
                    slave_title = slave_config["title"]
                    ios_config = slave_config.get("ios", {})

                    # Create slave instance
                    device_uid = port + "_" + str(slave_id)
                    self._device_registry.async_get_or_create(
                        config_entry_id=self._config_entry_id,
                        identifiers={(const.DOMAIN, device_uid)},
                        manufacturer="Scarfsail",
                        model="RSC_Slave",
                        name=slave_title,
                    )
                    slave = RscSlave(
                        slave_id,
                        slave_title,
                        ios_config,
                        self._entities_manager,
                        device_uid,
                        slave_telemetry_entities_id,
                    )
                    slaves.append(slave)  # Add to list instead of dictionary

                # Create master with its slaves
                master = RscMaster(communication_config, title, slaves)
                self._masters[port] = master
                self._logger.info(
                    f"Created master: {title} on port {port} with {len(slaves)} slaves"
                )

            self._entities_manager.create_entities()
            return True

        except Exception as e:
            self._logger.error(f"Error loading configuration: {e}")
            return False

    def start_all_masters(self) -> bool:
        """Start communication for all masters."""
        success = True
        for port, master in self._masters.items():
            if not master.begin_communication():
                self._logger.error(
                    f"Failed to start communication for master on port {port}"
                )
                success = False
        return success

    def stop_all_masters(self) -> None:
        """Stop communication for all masters."""
        for port, master in self._masters.items():
            master.stop_communication()
        self._logger.info("All masters stopped")
