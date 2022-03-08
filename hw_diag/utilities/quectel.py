import subprocess
import os
import urllib.request
import time
import dbus
import tarfile
from retry import retry
from retry.api import retry_call
from typing import Tuple

from hm_pyhelper.logger import get_logger
from hw_diag.utilities.dbus_proxy.dbus_ids import DBusIds
from hw_diag.utilities.dbus_proxy.modem_manager import ModemManager
from hw_diag.utilities.dbus_proxy.modem_manager import Modem
from hw_diag.utilities.dbus_proxy.systemd import Systemd
from hw_diag.utilities.keystore import KeyStore
from hw_diag.utilities.download import download_with_resume

logging = get_logger(__name__)

# quectel unique properties
EG25G_UNIQUE_PROPERTIES = {"Revision": ["EG25GGBR07A08M2G", "EG25GGBR07A07M2G"]}
MODEM_RESET_WAIT_TIME = 120
INTERNET_MAX_WAIT_TIME = 600

# latest firmware that is suppoed to fix AT&T 3G shutdown.
EG25G_OLD_KNOWN_FW = {
    "EG25GGBR07A08M2G": "EG25GGBR07A08M2G_01.001.01.001",
    "EG25GGBR07A07M2G": "EG25GGBR07A07M2G_01.001.01.001",
}

EG25G_DESIRED_FW = {
    "EG25GGBR07A08M2G": "EG25GGBR07A08M2G_30.006.30.006",
    "EG25GGBR07A07M2G": "EG25GGBR07A07M2G_30.003.30.003",
}

FW_FILE_HASH = {
    "EG25GGBR07A07M2G_01.001.01.001.tgz":
        "180bf41a3f08e5eb631d1ee98d1ff18dca14e6ef32ef9d41f704cc261ad163d0",
    "EG25GGBR07A07M2G_30.003.30.003.tgz":
        "7220c074d2abdcfa1d5e5740f9c8ad5561f09f294ce4e36bb6e05c9e3c0762dc",
    "EG25GGBR07A08M2G_01.001.01.001.tgz":
        "00c21f7843a12923265628a619fbea77876e393d51e94cf8f47e68aebf32a038",
    "EG25GGBR07A08M2G_30.006.30.006.tgz":
        "bde8796ae6307ecd31dce477d1a9281f67339ed0fbe4eee2d1ab108a061243b7",
}

GCP_FW_BASEPATH = (
    "https://storage.googleapis.com/helium-assets.nebra.com/modem-firmware/eg25g_firmware/"
)
FW_STATE_FILE = "/var/data/quectel_state"
FW_STORE_PATH = "/var/data/modem_firmware"
FW_MAX_RETRIES = 10
SETTINGS_MAX_RETRIES = 30


def get_feature_retry_count(feature: str) -> int:
    feature_history = KeyStore(FW_STATE_FILE)
    return feature_history.get(feature, 0)


def at_max_retries(feature: str, max_retries: int) -> bool:
    existing_retries = get_feature_retry_count(feature)
    if existing_retries >= max_retries:
        logging.warning(f"{feature} has already been tried {existing_retries} times")
        return True
    return False


def increment_retry_count(feature: str) -> None:
    feature_history = KeyStore(FW_STATE_FILE)
    existing_retries = feature_history.get(feature, 0)
    feature_history.set(feature, existing_retries + 1)


def find_eg25g_modem() -> Modem:
    mm_proxy = ModemManager()
    modem = mm_proxy.find_modem_by_properties(EG25G_UNIQUE_PROPERTIES)
    return modem


@retry(Exception, tries=3, delay=5, backoff=2, logger=logging)
def download_and_extract(url: str, file_path: str, file_hash: str) -> None:
    download_with_resume(url, file_path, file_hash)
    # sonar raises warning here for integrity check, in our case it doesn't hold
    # integrity is always checked when file is downloaded, thus NOSONAR
    with tarfile.open(file_path, "r:gz") as tar:  # NOSONAR
        tar.extractall(FW_STORE_PATH)
    os.remove(file_path)


def get_firmware_versions() -> list:
    """returns list of firmwar versions to be downloaded"""
    # Note:: it was decided that we would expect the miner to have internet connectivity
    # while installing the modem. That is why we check for modem and download fw for
    # that revision. If we want to download firmware for all revisions for all outdoor miner.
    # we will need to check VARIANT in a list of outdoor variant types and download firmware
    # assuming only outdoor ones have the option of a modem.
    fw_versions = []
    try:
        modem = find_eg25g_modem()
        if modem:
            modem_revision = modem.get_property("Revision")
            fw_versions.append(EG25G_OLD_KNOWN_FW[modem_revision])
            fw_versions.append(EG25G_DESIRED_FW[modem_revision])
    except Exception as e:
        logging.error(f"failed to determine required firmware revisions: {e}")

    return fw_versions


def download_modem_firmware(fw_versions: list) -> None:
    if not os.path.exists(FW_STORE_PATH):
        os.makedirs(FW_STORE_PATH)

    for fw_version in fw_versions:
        fw_file_name = fw_version + ".tgz"
        fw_dir_path = os.path.join(FW_STORE_PATH, fw_version)
        if os.path.isdir(fw_dir_path):
            logging.info(f"{fw_version} already present, skipping download")
            continue
        fw_file_path = os.path.join(FW_STORE_PATH, fw_file_name)
        fw_url = GCP_FW_BASEPATH + fw_file_name
        fw_hash = FW_FILE_HASH[fw_file_name]
        download_and_extract(fw_url, fw_file_path, fw_hash)


def reset_modem(modem: Modem) -> None:
    try:
        modem.reset()
    except Exception as e:
        logging.info(
            f"failed to reset modem: {e} modem was probably already reset/removed previously"
        )


def reset_modem_manager() -> None:
    # modem manager loses all track of the modem after reset, we need to restart it.
    systemd_proxy = Systemd()
    mm_unit = systemd_proxy.get_unit(DBusIds.MODEM_MANAGER_UNIT_NAME)
    mm_restarted = mm_unit.wait_restart()
    logging.info(f"modem manager restarted: {mm_restarted}")
    logging.info(
        f"waiting {MODEM_RESET_WAIT_TIME} seconds for the modem manager to pick the modem again"
    )
    time.sleep(MODEM_RESET_WAIT_TIME)


def reset_modem_and_modem_manager(modem: Modem) -> None:
    # try if modem is still valid.
    # a previous operation might have resulted in modem being reset/removed.
    reset_modem(modem)
    reset_modem_manager()


def _do_upgrade(desired_fw_version: str) -> bool:
    fw_dir = os.path.join(FW_STORE_PATH, desired_fw_version)
    if not os.path.isdir(fw_dir):
        logging.error(f"{fw_dir} does not exist")
        return False

    systemd_proxy = Systemd()
    mm_unit = systemd_proxy.get_unit(DBusIds.MODEM_MANAGER_UNIT_NAME)

    upgrade_successful = False

    stopped = mm_unit.wait_stop()
    logging.info(f"modem manager stopped: {stopped}")

    if stopped:
        flash_cmd = ["/usr/sbin/QFirehose", "-f"]
        flash_cmd.append(fw_dir)
        try:
            logging.info(f"executing {flash_cmd} to upgrade modem firmware")
            flash_cmd_output = subprocess.check_output(flash_cmd, stderr=subprocess.STDOUT)
            logging.info(f"qfirehose cmd output: {flash_cmd_output}")
            upgrade_successful = True
        except subprocess.CalledProcessError as e:
            logging.error(f"QFirehose failed with error: {e}")
        except Exception as e:
            logging.error(f"unknown error while trying to upgrade using QFirehose: {e}")

    # restart the modem manager
    mm_unit.wait_start()
    return upgrade_successful


def is_internet_accessible(wait_time: int = INTERNET_MAX_WAIT_TIME) -> bool:
    """wait for wait_time seconds for modem to achieve connectivity"""
    try:
        delay_interval = 5
        max_tries = wait_time / delay_interval
        retry_call(
            urllib.request.urlopen,
            fkwargs={"url": "https://google.com", "timeout": 3},
            tries=max_tries,
            delay=delay_interval,
            logger=logging,
        )
        return True
    except Exception as e:
        logging.info(f"internet not accessible: {e}")
        return False


def call_method(obj, method, *args, **kwargs):
    return getattr(obj, method)(*args, **kwargs)


def setting_needs_update(
    modem: Modem, getter: str, setter: str, desired_value: str
) -> Tuple[bool, str]:
    """
    getter and setter are called dynamically on Modem object using reflection.
    return a tuple containing:
    true if settings needs to be updated, false otherwise
    and current value of the setting
    """
    old_value = call_method(modem, getter)
    if at_max_retries(setter, SETTINGS_MAX_RETRIES):
        return False, old_value

    if old_value == desired_value:
        logging.info(f"Setting is already correct {old_value}")
        return False, old_value
    logging.info(f"actual value : {old_value} needs to be: {desired_value}")
    return True, old_value


def update_setting(modem: Modem, getter: str, setter: str, desired_value: str) -> bool:
    """
    getter and setter are called dynamically on Modem object using reflection.
    returns true if the setting was correctly updated, false otherwise
    """
    try:
        call_method(modem, setter, desired_value)
        new_value = call_method(modem, getter)
        if desired_value != new_value:
            logging.error("the value didn't set correctly")
            return False
        return True
    except Exception as e:
        logging.info(f"failed to update setting {setter} to {desired_value}")
        logging.error(f"error: {e}")
        return False


def update_setting_with_rollback(getter: str, setter: str, desired_value: str) -> bool:
    """
    update setting to desired value using getter and setter method on discovered modem.
    getter and setter are called dynamically using reflection.
    if setting update fails, roll back to old value is tried up to SETTINGS_MAX_RETRIES times.
    """
    try:
        modem = find_eg25g_modem()
        if not modem:
            logging.debug("EG25G modem not found")
            return False

        update_needed, old_value = setting_needs_update(modem, getter, setter, desired_value)
        if not update_needed:
            return False

        if not update_setting(modem, getter, setter, desired_value):
            return False

        internet_before_mode_change = is_internet_accessible()

        # we have verified the setting was set correctly, lets reset.
        reset_modem_and_modem_manager(modem)

        internet_after_mode_change = is_internet_accessible()

        # we had internet before but lost it, restore original value
        if internet_before_mode_change and not internet_after_mode_change:
            logging.error(f"internet lost after setting {desired_value}")
            modem = find_eg25g_modem()
            if not modem:
                logging.info("EG25G modem not found, setting old value will be skipped")
                return False
            increment_retry_count(setter)
            logging.info(f"resetting to {old_value}")
            update_setting(modem, getter, setter, old_value)
    except dbus.exceptions.DBusException as e:
        logging.error(f"failed to set AT over dbus with error: {e.get_dbus_message()}")
        return False
    except Exception as e:
        logging.error(f"failed to set AT Setting: {e}")
        return False
    return True


def firmware_upgrade_with_rollback() -> bool:
    modem = find_eg25g_modem()
    if not modem:
        logging.debug("EG25G modem not found")
        return False

    # upgrade
    modem_hw_revision = modem.get_property("Revision").strip()
    if modem_hw_revision not in EG25G_DESIRED_FW:
        logging.warning(
            f"no possible update for {modem_hw_revision} contact quectel for upgrades"
        )
        return False

    desired_fw_version = EG25G_DESIRED_FW[modem_hw_revision]
    current_fw = modem.get_fw_version()
    if current_fw == desired_fw_version:
        logging.info(f"modem is already at {current_fw}")
        return False

    if at_max_retries(desired_fw_version, FW_MAX_RETRIES):
        return False

    internet_before_upgrade = is_internet_accessible()
    modem_upgrade_status = _do_upgrade(desired_fw_version)
    logging.info(
        "modem upgrade status: {}".format("success" if modem_upgrade_status else "failure")
    )
    if not modem_upgrade_status:
        backup_firmware = EG25G_OLD_KNOWN_FW[modem_hw_revision]
        logging.error(
            f"firmware upgrade to {desired_fw_version} failed. reverting to {backup_firmware}"
        )
        _do_upgrade(backup_firmware)
        return False

    internet_after_upgrade = is_internet_accessible()
    if internet_before_upgrade and not internet_after_upgrade:
        backup_firmware = EG25G_OLD_KNOWN_FW[modem_hw_revision]
        logging.error(
            f"couldn't get internet connection after upgrade to {desired_fw_version}"
            f" reverting to {backup_firmware}"
        )
        # update retry count and revert to old firmware
        increment_retry_count(desired_fw_version)
        _do_upgrade(backup_firmware)
    return True


def ensure_modem_manager_health() -> None:
    # Note:: sometime modem manager is found stuck when balena
    # deploys new containers. If it is unresponsive we restart it.
    # before we attempt any changes to settings and firmware
    mm_proxy = ModemManager()
    all_modems = []
    try:
        all_modems = mm_proxy.get_all_modems()
    except Exception as e:
        logging.error(f"failed to get modem list with error: {e}")
        logging.error("most likely modem manager dbus interface is not responsive")

    if len(all_modems) == 0:
        reset_modem_manager()


def is_att_sim() -> bool:
    att_sim = False
    try:
        modem = find_eg25g_modem()
        if modem:
            sim = modem.get_sim()
            att_sim = sim.is_att_sim()
    except Exception as e:
        # no modem or no sim
        logging.info(f"failed to get sim info with error: {e}")
    return att_sim


def ensure_quectel_health() -> None:
    """
    ensure that modem manager is replying over dbus.
    download firmware files based on modem's hw revision.
    update modem's settings to Data Centric mode.
    if modem has AT&T SIM, update modem's firmware
    we are limiting firmware upgrade to AT&T SIM for now because we have seen
    in testing that firmware update can effect non at&t connectivity like T-Mobile
    only gets ipv6 after firmware update which can create problems for us.
    """
    # make sure modem manager is responsive
    ensure_modem_manager_health()

    # we want to download firmware files at the first possible opportunity.
    try:
        download_modem_firmware(get_firmware_versions())
    except Exception as e:
        logging.error(f"unknown error while downloading firmware: {e}")

    # ensure correct settings, these settings are recommended for data centric operation.
    # basically we are telling modem and network we are not interested in voice services.
    # this seems to work for most operators, making it default and not feature gated.
    try:
        logging.info("lets ensure that UE_MODE is set to DATA_CENTRIC")
        update_setting_with_rollback("get_ue_mode", "set_ue_mode", Modem.UE_MODE_DATA_ONLY_VALUE)
        logging.info("lets ensure that service domain is PS")
        update_setting_with_rollback(
            "get_service_domain", "set_service_domain", Modem.SERVICE_DOMAIN_PS_VALUE
        )
    except Exception as e:
        logging.error(f"unknown error, failed to do correct mode setting: {e}")

    if not os.getenv("UPDATE_QUECTEL_EG25G_MODEM", False):
        logging.info(
            "skipping quectel firmware update because UPDATE_QUECTEL_EG25G_MODEM is not set"
        )
        return

    # Note:: Till such time we figure out balena ipv6 issues fully. Lets keep this check
    if not is_att_sim():
        logging.info("skipping firmware upgrade as att sim was not found")
        return

    # update firmware
    fw_status = firmware_upgrade_with_rollback()
    if fw_status:
        logging.info("modem firmware upgrade successful")
