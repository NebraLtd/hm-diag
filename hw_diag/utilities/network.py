from hw_diag.utilities.balena_supervisor import BalenaSupervisor


def get_device_hostname():
    try:
        balena_supervisor = BalenaSupervisor.new_from_env()
        device_config = balena_supervisor.get_device_config()
        network = device_config.get('network')
        hostname = network.get('hostname')
    except Exception:
        hostname = None
    return hostname
