from __future__ import annotations
import logging
import os
import tempfile
from typing import Dict
from uptime import uptime
from datetime import timedelta, datetime
from logging.handlers import RotatingFileHandler
from hm_pyhelper.logger import get_logger
from icmplib import ping
from hw_diag.utilities.balena_supervisor import BalenaSupervisor
from hw_diag.utilities.dbus_proxy.dbus_ids import DBusIds
from hw_diag.utilities.dbus_proxy.network_manager import NetworkManager
from hw_diag.utilities.dbus_proxy.systemd import Systemd
from hw_diag.utilities.event_streamer import EVENT_TYPE_KEY, ACTION_TYPE_KEY, \
    DiagEvent, DiagAction, event_streamer, event_fingerprint
from hw_diag.utilities import system_metrics

LOGLEVEL = os.environ.get("LOGLEVEL", "DEBUG")
_log_format = "%(asctime)s - [%(levelname)s] - (%(filename)s:%(lineno)d) - %(message)s"


class NetworkWatchdog:
    VOLUME_PATH = '/var/watchdog/'
    WATCHDOG_LOG_FILE_NAME = 'watchdog.log'
    MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 Mb

    # Failed connectivity count for the network manager to restart
    NM_RESTART_THRESHOLD = int(os.environ.get("NM_RESTART_THRESHOLD", 1))
    # Failed connectivity count for the hotspot to reboot
    FULL_REBOOT_THRESHOLD = int(os.environ.get("FULL_REBOOT_THRESHOLD", 3))
    # Failed reboot count for the hotspot to reboot forcibly
    FULL_FORCE_REBOOT_THRESHOLD = int(os.environ.get("FULL_FORCE_REBOOT_THRESHOLD", 3))
    # Full system reboot limited to once a day
    REBOOT_LIMIT_HOURS = int(os.environ.get("REBOOT_LIMIT_HOURS", 24))

    PUBLIC_SERVERS = ['8.8.8.8', '1.1.1.1']       # NOSONAR

    # Static variable for saving the lost connectivity count
    lost_count = 0

    # Static variable for saving the failed reboot count
    reboot_request_count = 0

    last_network_event = DiagEvent.NETWORK_DISCONNECTED
    last_network_action = DiagAction.ACTION_NONE
    last_network_event_fingerprint = ""

    def __init__(self):
        # Prepare the log file location
        if os.access(self.VOLUME_PATH, os.W_OK):
            self.log_file_path = os.path.join(self.VOLUME_PATH, self.WATCHDOG_LOG_FILE_NAME)
        else:
            self.temp_dir = tempfile.TemporaryDirectory()
            self.log_file_path = os.path.join(self.temp_dir.name, self.WATCHDOG_LOG_FILE_NAME)

        # Set up logger
        self.LOGGER = get_logger(__name__)
        # Add rotating log handler to the logger
        handler = RotatingFileHandler(self.log_file_path, maxBytes=self.MAX_LOG_SIZE, backupCount=3)
        handler.setLevel(LOGLEVEL)
        handler.setFormatter(logging.Formatter(_log_format))
        self.LOGGER.addHandler(handler)

    def __del__(self):
        if hasattr(self, 'temp_dir'):
            self.temp_dir.cleanup()

    def is_ping_reachable(self, ip: str) -> bool:
        try:
            ping_target = ping(ip)
            reachable = ping_target and ping_target.address == ip and ping_target.is_alive
            if reachable:
                self.LOGGER.info(f'{ip} is reachable.')
            else:
                self.LOGGER.info(f'{ip} is not reachable.')
            return reachable
        except Exception:
            return False

    def is_local_network_connected(self) -> bool:
        network_manager = NetworkManager()
        gateways = network_manager.get_gateways()
        for gateway in gateways:
            if self.is_ping_reachable(gateway):
                return True
        return False

    def is_internet_connected(self) -> bool:
        for public_server in self.PUBLIC_SERVERS:
            if self.is_ping_reachable(public_server):
                return True
        return False

    def is_connected(self) -> bool:
        is_local_network_connected = self.is_local_network_connected()
        self.LOGGER.info(f"Local network connection: {is_local_network_connected}")

        is_internet_connected = self.is_internet_connected()
        self.LOGGER.info(f"Internet connection: {is_internet_connected}")

        return is_local_network_connected

    def restart_network_manager(self) -> None:
        """Restart hostOS NetworkManager service"""
        systemd_proxy = Systemd()
        network_manager_unit = systemd_proxy.get_unit(DBusIds.NETWORK_MANAGER_UNIT_NAME)
        nm_restarted = network_manager_unit.wait_restart()
        self.LOGGER.info(f"Network manager restarted: {nm_restarted}")

    def _prepare_event(self, event_type: DiagEvent,
                       action_type: DiagAction, msg: str) -> Dict:
        network_stats = system_metrics.get_network_statistics()
        event = {
            # using names instead of values as our models have enums as strings
            EVENT_TYPE_KEY: event_type.name,
            ACTION_TYPE_KEY: action_type.name,
            'msg': msg,
            'serial': system_metrics.get_serial_number(),
            'variant': system_metrics.get_variant(),
            'firmware_version': system_metrics.get_firmware_version(),
            'region_override': system_metrics.get_region_override(),
            # uptime in hours rounded to two decimal places
            'uptime_hours': round(float(uptime())/3600, 2),
            'packet_errors': system_metrics.total_packet_errors(network_stats),
            'generated_ts': datetime.utcnow().timestamp(),
            'network_state': self.get_current_network_state().name
        }
        event.update(system_metrics.get_balena_metrics())
        return event

    def _send_network_event(self, event_type: DiagEvent,
                            action_type: DiagAction, msg: str) -> None:
        # don't repeat the events unnecessarily
        new_fingerprint = event_fingerprint(event_type, action_type, msg)
        if new_fingerprint == self.last_network_event_fingerprint:
            return

        # save last state
        self.last_network_event_fingerprint = new_fingerprint
        self.last_network_event = event_type
        self.last_network_action = action_type

        event = self._prepare_event(event_type, action_type, msg)
        event_streamer.enqueue_persistent_event(event)

    def get_current_network_state(self) -> DiagEvent:
        if self.is_internet_connected():
            return DiagEvent.NETWORK_INTERNET_CONNECTED
        elif self.is_local_network_connected():
            return DiagEvent.NETWORK_LOCAL_CONNECTED
        else:
            return DiagEvent.NETWORK_DISCONNECTED

    def emit_heartbeat(self) -> None:
        event = self._prepare_event(DiagEvent.HEARTBEAT, DiagAction.ACTION_NONE, "")
        event_streamer.enqueue_event(event)

    def ensure_network_connection(self) -> DiagEvent:
        self.LOGGER.info("Ensuring the network connection...")

        up_time = timedelta(seconds=uptime())
        self.LOGGER.info(f"OS has been up for {up_time}")

        network_state_event = self.get_current_network_state()

        # If network is connected, nothing to do more
        if network_state_event != DiagEvent.NETWORK_DISCONNECTED:
            self.lost_count = 0
            msg = "Network is working."
            self.LOGGER.info(msg)
            self._send_network_event(network_state_event, DiagAction.ACTION_NONE, msg)
            return network_state_event

        # If network is not working, take the next step
        self.lost_count += 1
        self.LOGGER.warning(
            f"Network is not connected! Lost connectivity count={self.lost_count}")

        if self.lost_count >= self.FULL_REBOOT_THRESHOLD:
            self.LOGGER.warning(
                "Reached threshold for system reboot to recover network.")
            if up_time < timedelta(hours=self.REBOOT_LIMIT_HOURS):
                msg = f"Hotspot has been restarted already within {self.REBOOT_LIMIT_HOURS}hour(s)."
                " Skip the rebooting."
                self.LOGGER.info(msg)
                self._send_network_event(network_state_event,
                                         DiagAction.ACTION_NONE, msg)
                return network_state_event

            force_reboot = self.reboot_request_count >= self.FULL_FORCE_REBOOT_THRESHOLD

            action = DiagAction.ACTION_SYSTEM_REBOOT
            if force_reboot:
                action = DiagAction.ACTION_SYSTEM_REBOOT_FORCED

            msg = f"Rebooting the hotspot(force={force_reboot})."
            self.LOGGER.info(msg)
            self._send_network_event(network_state_event, action, msg)

            self.reboot_request_count += 1
            self.LOGGER.info(f"Reboot request count={self.reboot_request_count}.")

            balena_supervisor = BalenaSupervisor.new_from_env()
            balena_supervisor.reboot(force=force_reboot)
        elif self.lost_count >= self.NM_RESTART_THRESHOLD:
            msg = "Reached threshold for Network Manager restart to recover network."
            self.LOGGER.warning(msg)
            self._send_network_event(network_state_event,
                                     DiagAction.ACTION_NM_RESTART,
                                     msg)
            self.restart_network_manager()
        return network_state_event


if __name__ == '__main__':
    watchdog = NetworkWatchdog()
    watchdog.ensure_network_connection()
