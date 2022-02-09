import subprocess
import os

from hm_pyhelper.logger import get_logger
from hw_diag.utilities.dbus_proxies import ModemManager, Systemd, Unit

logging = get_logger(__name__)

# quectel unique properties
EG25G_UNIQUE_PROPERTIES = { 
    'Manufacturer' : 'QUALCOMM INCORPORATED',
    'Model' : 'QUECTEL Mobile Broadband Module',
    'Revision' : 'EG25GGBR07A08M2G' }

# latest firmware that is suppoed to fix AT&T 3G shutdown.
KNOWN_GOOD_FW  = 'EG25GGBR07A08M2G_30.006.30.006'


def _do_upgrade(desired_fw_version):
    systemd_proxy = Systemd()
    mm_unit = systemd_proxy.get_unit('ModemManager.service')
    
    stopped = mm_unit.wait_stop()
    logging.info(f"modem manager stopped: {stopped}")
    
    if stopped:
        flash_cmd = ['/usr/sbin/QFirehose', '-f']
        flash_cmd.append(f'quectel/firmware/eg25-g/{desired_fw_version}')   
        try:
            logging.info(f'executing {flash_cmd} to upgrade modem firmware')
            subprocess.check_output(flash_cmd)
        except CalledProcessError as e:
            logging.error(f'QFirehose failed with error: {e}')
    
    # NOTE:: help from python experts, how do I make sure that  start() always happens
    mm_unit.start()

def ensure_quectel_health():
    '''
    proceed only if model is quectel eg25g
    stop modem manager
    upgrade firmware
    start modem manager
    ensure currect mode settings
    '''
    
    mm_proxy = ModemManager()
    
    # proceed only if we have EG25_G firmware
    modem = mm_proxy.find_modem_by_properties(EG25G_UNIQUE_PROPERTIES)
    if not modem:
        logging.debug('EG25G modem not found') 
        return

    # upgrade
    if not os.getenv('BALENA_SKIP_QUECTEL_UPDATE', False):
        desired_fw_version = os.getenv('BALENA_QUECTEL_FW_VERSION', KNOWN_GOOD_FW)
        current_fw = modem.get_fw_version()
        if current_fw == desired_fw_version:
            logging.info('modem is already at {current_fw}')
        else:
            _do_upgrade(desired_fw_version)
    
    # ensure correct settings
    modem.ensure_data_centric_mode()

