import dbus
import logging
from time import sleep


def get_public_keys():
    """
    get three public keys
    PK - The public key of the miner
    OK - The Onboarding key of the miner
    AN - The Animal Name of the miner
    from file "/var/data/public_keys"
    A list of keys will be returned.
    """
    pk_file = None
    while pk_file is None:
        try:
            pk_file = open("/var/data/public_keys").readline().split('"')[1::2]
        except FileNotFoundError:
            sleep(10)
        except PermissionError:
            raise PermissionError(
                "/var/data/public_keys no permission to read the file"
            )

    return pk_file


def get_miner_diagnostics():
    # Get miner diagnostics
    # return MC - MD - MH - MN list
    param_list = []
    try:
        miner_bus = dbus.SystemBus()
        miner_object = miner_bus.get_object('com.helium.Miner', '/')
        miner_interface = dbus.Interface(miner_object, 'com.helium.Miner')
        try:
            p2pstatus = miner_interface.P2PStatus()
            param_list = [
                str(p2pstatus[0][1]),
                str(p2pstatus[1][1]),
                str(p2pstatus[3][1]),
                str(p2pstatus[2][1])
            ]
        except dbus.exceptions.DBusException as e:
            raise dbus.exceptions.DBusException(e)
    except (Exception, dbus.exceptions.DBusException):
        param_list = [
            "no",
            "",
            "0",
            ""
        ]

    return param_list


def write_public_keys_to_diag(data, diagnostics):
    # The order of the values in the list is important!
    # It determines which value will be available for which key
    if data is not None and len(data) == 3:
        keys = ["PK", "OK", "AN"]
        for (param, key) in zip(data, keys):
            diagnostics[key] = param
    else:
        logging.error(
            "The public keys from the file were obtained with an unknown error"
        )


def set_param_miner_diag(diagnostics):
    # The order of the values in the list is important!
    # It determines which value will be available for which key
    param_miner_diag = get_miner_diagnostics()
    keys = ['MC', 'MD', 'MH', 'MN']
    for (param, key) in zip(param_miner_diag, keys):
        diagnostics[key] = param
