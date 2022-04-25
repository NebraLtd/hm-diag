import logging
import datetime
import json
from typing import Any

from hm_pyhelper.hardware_definitions import variant_definitions
from hm_pyhelper.miner_param import get_ethernet_addresses
from hw_diag.diagnostics.lte_diagnostic import LOGGER
from hw_diag.utilities.hardware import detect_ecc
from hw_diag.utilities.hardware import get_serial_number
from hw_diag.utilities.hardware import lora_module_test
from hw_diag.utilities.hardware import set_diagnostics_bt_lte
from hw_diag.utilities.hardware import get_public_keys_and_ignore_errors
from hw_diag.utilities.shell import get_environment_var
from hw_diag.utilities.gcs_shipper import upload_diagnostics
from hw_diag.diagnostics.gateway_diagnostics import GatewayDiagnostic
from hm_pyhelper.diagnostics import DiagnosticsReport


log = logging.getLogger()
log.setLevel(logging.DEBUG)


def get_deep_key(source_dict: dict, key_path: list) -> Any:
    """
    Returns None if any part of the key in key_path is not found in source_dict else the value
    """
    try:
        for key in source_dict:
            source_dict = source_dict[key]
        return source_dict
    except KeyError as err:
        LOGGER.exception(f"expected key not found {err}")
        return None


def perform_hw_diagnostics(ship=False):  # noqa: C901
    log.info('Running periodic hardware diagnostics')

    diagnostics = [
        GatewayDiagnostic()
    ]

    diagnostics_report = DiagnosticsReport(diagnostics)
    diagnostics_report.perform_diagnostics()

    # TODO:: message should change once all the functions have been
    # converted to diagnostics.
    LOGGER.debug("partial refactored diagnostics report is: %s" % diagnostics_report)

    diagnostics = diagnostics_report

    now = datetime.datetime.utcnow()
    diagnostics['last_updated'] = now.strftime("%H:%M UTC %d %b %Y")

    get_ethernet_addresses(diagnostics)
    get_environment_var(diagnostics)
    get_serial_number(diagnostics)
    detect_ecc(diagnostics)
    public_keys = get_public_keys_and_ignore_errors()

    diagnostics['LOR'] = lora_module_test()
    diagnostics['OK'] = public_keys['key']
    diagnostics['PK'] = public_keys['key']
    diagnostics['AN'] = public_keys['name']

    set_diagnostics_bt_lte(diagnostics)

    # Check the basics if they're fine and set an overall value
    # Basics are: ECC valid, Mac addresses aren't FF, BT Is present,
    # and LoRa hasn't failed
    if (
            diagnostics["ECC"] is True
            and diagnostics["E0"] is not None
            and diagnostics["W0"] is not None
            and diagnostics["BT"] is True
            and diagnostics["LOR"] is True
            and get_deep_key(diagnostics, ["gatewayrs", "validator_uri"]) is not None
    ):
        diagnostics["PF"] = True
    else:
        diagnostics["PF"] = False

    # Add variant variables into diagnostics
    # These are variables from the hardware definitions file
    try:
        variant_variables = variant_definitions[diagnostics['VA']]
        diagnostics.update(variant_variables)
    except KeyError:
        pass

    with open('diagnostic_data.json', 'w') as f:
        json.dump(diagnostics, f)

    upload_diagnostics(diagnostics, ship)

    log.info('Diagnostics complete')
