import os
import json
import subprocess
import requests
from hw_diag.utilities.osutils import balena_boot_partition
from hw_diag.utilities.hardware import get_serial_number
from hw_diag.utilities.balena_supervisor import BalenaSupervisor
from hm_pyhelper.logger import get_logger
from typing import Dict, Union

# constants
BOOT_MOUNT_POINT = '/tmp/boot'
CONFIG_FILENAME = f'{BOOT_MOUNT_POINT}/config.json'
CONFIG_TEMP_FILENAME = f'{CONFIG_FILENAME}_temp'

# env vars
DASHBOARD_ENDPOINT = os.getenv('DASHBOARD_DEVICE_CONFIG_ENDPOINT',
                               'https://dashboard.nebra.com/api/v0.1/device/config'
                               )
TOKEN = os.getenv('NEBRAOS_MIGRATION_TOKEN',
                  'cbe1291fbb3e59cc326e2b8eba8e2e0b932e77bf')


LOGGER = get_logger(__name__)


def attempt_device_migration():
    if not TOKEN:
        LOGGER.warning("NEBRAOS_MIGRATION_TOKEN should be provided by environment")
        return

    # read config.json
    old_config = read_config()

    # update appid from env as config.json always contains appid of fleet
    # where it was created
    creation_app_id = old_config['applicationId']
    old_config['applicationId'] = os.getenv("BALENA_APP_ID", creation_app_id)

    # update config with values from dashboard
    new_config = update_config(old_config)

    # no updates from dashboard.
    if not new_config:
        LOGGER.info("no updates to config")
        return

    LOGGER.info(f"used appid: {old_config['applicationId']} for config.json updates")
    # migration fixups
    if is_cloud_migration(old_config, new_config):
        if 'initialDeviceName' not in new_config:
            # balena instance migration and initial device name is not set.
            # set a sensible default
            new_config['initialDeviceName'] = migrated_dev_name()

    if old_config == new_config:
        LOGGER.warning("new configuration is same as old. not writing")
        return

    write_config(new_config)


def migrated_dev_name() -> str:
    return f'{fetch_serial_number()}-automigrated'


def is_cloud_migration(old_config, new_config) -> bool:
    return old_config['apiEndpoint'] != new_config['apiEndpoint']


def update_config(old_config) -> Union[Dict, None]:
    """
    Return new config if update is required otherwise None is returned
    """
    serial_number = fetch_serial_number()
    if not serial_number:
        return None
    r = requests.patch(
        f'{DASHBOARD_ENDPOINT}/{serial_number}',
        json=old_config, headers={"Authorization": f"token {TOKEN}"}
    )
    if r.status_code == 204:
        LOGGER.info("no update needed")
        return None
    elif r.status_code != 200:
        LOGGER.error(f"error code from server: {r.status_code}")
        return None

    # update values
    LOGGER.warning(f"performing update operation for: {CONFIG_FILENAME}")
    new_config = old_config.copy()
    updates = r.json()
    if 'write' in updates:
        new_config.update(updates['write'])

    # remove keys if required
    for k in updates['remove']:
        if k in new_config:
            new_config.pop(k)

    return new_config


def fetch_serial_number() -> Union[str, None]:
    diag = {}
    get_serial_number(diag)
    return diag.get("serial_number")


def read_config() -> Dict:
    # read only mount would have been great but that isn't
    # possible as the fs is mounted in host os as rw.
    mount_boot_partition()
    config_data = json.load(open(CONFIG_FILENAME, 'r'))
    unmount_boot_partition()
    return config_data


def write_config(config_data: Dict):
    try:
        mount_boot_partition()
        LOGGER.warning("writing config.json, potentially dangerous")
        with open(CONFIG_TEMP_FILENAME, 'w') as f:
            f.write(json.dumps(config_data))
        os.replace(CONFIG_TEMP_FILENAME, CONFIG_FILENAME)
        # if we are writing to the file, we need to reboot.
        # not rebooting immediately leaves us vulnerable to corruption
        # by os-config or something else we might not know about in balena.
        # WARNING:: did think of a roll back scenario if reboot fails. But
        # not sure if it has any value, I think a manual reboot might still bring the
        # device back to migrated cloud. And updates are not always about migration.
        balena_supervisor = BalenaSupervisor.new_from_env()
        balena_supervisor.reboot(force=True)
    except Exception as e:
        LOGGER.error(f"failed to write {CONFIG_FILENAME}")
        LOGGER.error(f"reported error: {e}")
    unmount_boot_partition()


def mount_boot_partition(mount_rw: bool = True):
    boot_part = balena_boot_partition()
    mount_device(boot_part, BOOT_MOUNT_POINT)


def mount_device(device: str, path: str, mount_rw: bool = True):
    if not os.path.exists(path):
        os.mkdir(path)

    if os.path.ismount(path):
        mount_option = 'remount,rw' if mount_rw else 'remount,ro'
    else:
        mount_option = 'rw' if mount_rw else 'ro'

    cmd = ["mount", "-o", mount_option, device, path]
    subprocess.check_call(cmd)


def unmount_boot_partition():
    unmount_path(BOOT_MOUNT_POINT)


def unmount_path(path: str):
    """
    Unmount the fs from path if it is mounted
    """
    try:
        if os.path.ismount(path):
            subprocess.check_call(["umount", path])
    except subprocess.CalledProcessError as e:
        LOGGER.error(f'failed to unmount {e}')


if __name__ == '__main__':
    attempt_device_migration()
