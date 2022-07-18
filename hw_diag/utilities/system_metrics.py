from typing import Dict, Any, Union
import logging
import os
import json
from balena_supervisor import BalenaSupervisor

log = logging.getLogger()


def get_failed_services(container_list) -> list:
    failed_list = []
    for container in container_list:
        if container["status"] != "Running":
            failed_list.append(container["serviceName"])
    return failed_list


def get_balena_metrics() -> Dict:
    try:
        supervisor = BalenaSupervisor.new_from_env()
        app_state = json.loads(supervisor.get_application_state())
        # app_state = json.loads('{"status":"success","appState":"applied","overallDownloadProgress":null,"containers":[{"status":"Running","serviceName":"packet-forwarder","appId":1803709,"imageId":5147947,"serviceId":952414,"containerId":"11fda396392c86ddaa394b9455b987f491f97bb07d4615ac2d60c6a05802650a","createdAt":"2022-07-15T00:20:01.011Z"},{"status":"Running","serviceName":"helium-miner","appId":1803709,"imageId":5147949,"serviceId":952412,"containerId":"0cb4f1c07c54d3f56e1f68e2f2f50f4f3312f9da0bdcaaa73571e80e92314be4","createdAt":"2022-07-15T00:19:55.693Z"},{"status":"Running","serviceName":"gateway-config","appId":1803709,"imageId":5147946,"serviceId":952413,"containerId":"89b7cbbbb221d1643681266aa44f4d42a6963cc6d734c42794cb3bfcc2474e5a","createdAt":"2022-07-15T00:19:50.221Z"},{"status":"Running","serviceName":"diagnostics","appId":1803709,"imageId":5147948,"serviceId":952411,"containerId":"e5af0b42372bdea0f7c3f84981aa9fec853a1e9eff4839ecf43bdfbee672ad33","createdAt":"2022-07-15T00:19:40.688Z"},{"status":"Running","serviceName":"dbus-session","appId":1803709,"imageId":5147950,"serviceId":1254941,"containerId":"49e907602cf037ba90b34680096702a65fdb136abd31fe0eb117460fb7abebc8","createdAt":"2022-07-15T00:19:34.312Z"}],"images":[{"name":"registry2.balena-cloud.com/v2/3c411a031691b34e9b6cab7f011cf283@sha256:8dc540aa5b7c37dbef893e3431ef2abffe471b87e6f45b27333af3451ad3c389","appId":1803709,"serviceName":"packet-forwarder","imageId":5147947,"dockerImageId":"sha256:166b6ba191144704aad64dd41e11a5891ccee984cc051ad11ac061521f3d699d","status":"Downloaded"},{"name":"registry2.balena-cloud.com/v2/6914df919737837f9a265d55c4376f33@sha256:2563460fcbcb7b4945c51bbaf5f08a07c13a430cad70750ee8bddcd79dbead8d","appId":1803709,"serviceName":"diagnostics","imageId":5147948,"dockerImageId":"sha256:987c7df9cf51ab36d3e82ffe72d77887f8fdda4669993e1a2bc58e3d362777fc","status":"Downloaded"},{"name":"registry2.balena-cloud.com/v2/2190666213d12ed877ab0590fd1c147c@sha256:b8aff177b71416d5a6e145a8aadd4c76f7bb667fcf4ff6f83f02ab33e9bfe8ca","appId":1803709,"serviceName":"gateway-config","imageId":5147946,"dockerImageId":"sha256:617330ab48c129520e161a7ec07b3974404dfc6b6a98e89cdedef65c9c692899","status":"Downloaded"},{"name":"registry2.balena-cloud.com/v2/a664e01d02bd0da73f6b3d838d3d9c1f@sha256:ad1f0b44c65aa9749e083174098bd4a82f97267a753d3032c0dd70ca89d52e23","appId":1803709,"serviceName":"dbus-session","imageId":5147950,"dockerImageId":"sha256:5ce1dc1fad6f5463b34a40dc1ecb790280855fa69a3998efb8324a7bcf5d018f","status":"Downloaded"},{"name":"registry2.balena-cloud.com/v2/557bce89505e59ea63399846130b75ed@sha256:1cbb4ffc274e40c54fae728314a347b5f421ac9b70edd8fe1bb7f40234e7bc38","appId":1803709,"serviceName":"helium-miner","imageId":5147949,"dockerImageId":"sha256:f5a919b0222d5d6a177f26675feb39d2c582831d44865e168a762b370205d1e2","status":"Downloaded"}],"release":"8575a4193de1739b8b6651f4f575ab0b"}')
    except Exception as e:
        log.error(f"error while getting container state from supervisor {e}")
        return {"status": "error"}

    if app_state["status"] != "success":
        log.error("container is reporting ")
        return {"status": "error"}

    metrics = {}
    if (app_state["status"] == "success"):
        metrics["balena_app_state"] = app_state["appState"]
        metrics["balena_release"] = app_state["release"]
        metrics["balena_failed_containers"] = get_failed_services(app_state["containers"])
        metrics["balena_all_running"] = len(metrics["balena_failed_containers"]) == 0
    else:
        metrics["balena_app_state"] = ""
        metrics["balena_release"] = ""
        metrics["balena_failed_containers"] = []
        metrics["balena_all_running"] = False
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
