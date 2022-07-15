from typing import Dict, Any, Union
import logging
import os
import json
from balena_supervisor import BalenaSupervisor

log = logging.getLogger()


def get_balena_metrics() -> Dict:
    try:
        supervisor = BalenaSupervisor.new_from_env()
        app_state = json.loads(supervisor.get_application_state())
    except Exception as e:
        log.error(f"error while getting container state from supervisor {e}")
        return {"status": "error"}

    if app_state["status"] != "success":
        log.error("container is reporting ")
        return {"status": "error"}

    metrics = {}
    metrics["status"] = app_state["status"]
    if (metrics["status"] == "success"):
        metrics["containers"] = app_state["containers"]
        metrics["release"] = app_state["release"]
    return metrics


def read_proc_file(file_path: str, default_value: Union[str, int]) -> Any:
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        log.warning(f"can't read proc file {file_path} {e}")
        return default_value


def get_serial_number() -> str:
    try:
        with open("/proc/device-tree/serial-number", 'r') as f:
            return f.readline().rstrip('\x00')
    except Exception as e:
        log.warning(f"can't read serial number {e}")
        return ""


def get_variant() -> str:
    return os.getenv('VARIANT', "")


def get_region_override() -> str:
    return os.getenv('REGION_OVERRIDE', "")


def get_firmware_version() -> str:
    return os.getenv('FIRMWARE_VERSION', "")


def get_network_statistics(interface_list=['wlan0', 'eth0']) -> Dict:
    stats = {}
    for iface_name in interface_list:
        stats[iface_name] = {
            "rx_errors": int(read_proc_file(f"/sys/class/net/{iface_name}/statistics/rx_bytes", 0)),
            "tx_errors": int(read_proc_file(f"/sys/class/net/{iface_name}/statistics/tx_bytes", 0))
        }
    return stats


def total_packet_errors(network_stats):
    total_errors = 0
    for iface in network_stats.keys():
        total_errors += network_stats[iface]["rx_errors"] + network_stats[iface]["tx_errors"]
    return total_errors


def are_all_services_up(balena_state: dict):
    if balena_state["status"] != "success":
        return False

    for service in balena_state["containers"]:
        if service["status"] != "Running":
            return False
    return True


if __name__ == "__main__":
    # print(get_balena_metrics())
    pass
