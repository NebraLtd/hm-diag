from typing import Dict, Any
import logging
import os
from hw_diag.utilities.hardware import fetch_serial_number
from hw_diag.utilities.balena_supervisor import BalenaSupervisor


log = logging.getLogger()


def get_failed_services(container_list: list) -> list:
    failed_list = []
    for container in container_list:
        if container["status"] != "Running":
            failed_list.append(container["serviceName"])
    return failed_list


def get_balena_metrics() -> Dict:
    try:
        supervisor = BalenaSupervisor.new_from_env()
        app_state = supervisor.get_device_status()
    except Exception as e:
        log.error(f"error while getting container state from supervisor {e}")
        return {"balena_api_status": "error", "balena_failed_containers": []}

    if app_state["status"] != "success":
        log.error("balena api is failing")

    metrics = {}
    metrics["balena_api_status"] = app_state["status"]
    # being a REPEATED field Biqquery doesn't allow it be missing
    metrics["balena_failed_containers"] = []
    if (app_state["status"] == "success"):
        metrics["balena_app_state"] = app_state["appState"]
        metrics["balena_release"] = app_state["release"]
        metrics["balena_failed_containers"] = get_failed_services(app_state["containers"])
        metrics["balena_all_running"] = len(metrics["balena_failed_containers"]) == 0
    return metrics


def read_proc_file(file_path: str, default_value: str) -> Any:
    try:
        with open(file_path, 'r') as f:
            return f.read()
    except Exception as e:
        log.warning(f"can't read proc file {file_path} {e}")
        return default_value


def get_serial_number() -> str:
    '''
    returns a valid serial number or empty string if none can
    be determined. No exceptions.
    '''
    try:
        serial_number = fetch_serial_number()
        if not serial_number:
            serial_number = ""
        return serial_number
    except Exception as e:
        log.error(f"failed to get serial number {e}")
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
            "rx_errors": int(
                read_proc_file(f"/sys/class/net/{iface_name}/statistics/rx_errors", "0")
            ),
            "tx_errors": int(
                read_proc_file(f"/sys/class/net/{iface_name}/statistics/tx_errors", "0")
            )
        }
    return stats


def total_packet_errors(network_stats):
    total_errors = 0
    for iface in network_stats.keys():
        total_errors += network_stats[iface]["rx_errors"] + network_stats[iface]["tx_errors"]
    return total_errors
