import json
import base64
import os
import logging

from flask import Blueprint, request
from flask import render_template, Response
from flask import jsonify
from datetime import datetime
from hm_pyhelper.constants.shipping import DESTINATION_ADD_GATEWAY_TXN_KEY
from hw_diag.diagnostics.shutdown_gateway_diagnostic import SHUTDOWN_GATEWAY_KEY
from hw_diag.cache import cache
from hm_pyhelper.diagnostics.diagnostics_report import DiagnosticsReport

from hw_diag.diagnostics.add_gateway_txn_diagnostic import AddGatewayTxnDiagnostic
from hw_diag.diagnostics.shutdown_gateway_diagnostic import ShutdownGatewayDiagnostic
from hw_diag.diagnostics.provision_key_diagnostic import ProvisionKeyDiagnostic

from hw_diag.diagnostics.ecc_diagnostic import EccDiagnostic
from hw_diag.diagnostics.env_var_diagnostics import EnvVarDiagnostics
from hw_diag.diagnostics.mac_diagnostics import MacDiagnostics
from hw_diag.diagnostics.serial_number_diagnostic import SerialNumberDiagnostic
from hw_diag.diagnostics.bt_diagnostic import BtDiagnostic
from hw_diag.diagnostics.lte_diagnostic import LteDiagnostic
from hw_diag.diagnostics.lora_diagnostic import LoraDiagnostic
from hw_diag.diagnostics.pf_diagnostic import PfDiagnostic
from hw_diag.diagnostics.key_diagnostics import KeyDiagnostics
from hw_diag.diagnostics.device_status_diagnostic import DeviceStatusDiagnostic
from hw_diag.utilities.diagnostics import compose_diagnostics_report_from_err_msg
from hw_diag.utilities.hardware import should_display_lte
from hm_pyhelper.logger import get_logger
from hw_diag.utilities.security import GnuPG
from hw_diag.utilities.auth import authenticate
from hw_diag.utilities.diagnostics import read_diagnostics_file


logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

LOGGER = get_logger(__name__)
DIAGNOSTICS = Blueprint('DIAGNOSTICS', __name__)


@DIAGNOSTICS.route('/json')
@cache.cached(timeout=60)
def get_diagnostics_json():
    diagnostics = read_diagnostics_file()
    response = jsonify(diagnostics)
    response.headers.set('Content-Disposition',
                         'attachment;filename=nebra-diag.json'
                         )
    response.headers.set('X-Robots-Tag', 'none')

    return response


@DIAGNOSTICS.route('/')
@authenticate
def get_diagnostics():
    diagnostics = read_diagnostics_file()
    display_lte = should_display_lte(diagnostics)
    now = datetime.utcnow()
    template_filename = 'diagnostics_page_light_miner.html'

    response = render_template(
        template_filename,
        diagnostics=diagnostics,
        display_lte=display_lte,
        now=now
    )

    return response


@DIAGNOSTICS.route('/initFile.txt')
@cache.cached(timeout=15)
def get_initialisation_file():
    """
    This needs to be generated as quickly as possible,
    so we bypass the regular timer.
    """

    diagnostics = [
        SerialNumberDiagnostic(),
        EccDiagnostic(),
        MacDiagnostics(),
        EnvVarDiagnostics(),
        BtDiagnostic(),
        LteDiagnostic(),
        LoraDiagnostic(),
        KeyDiagnostics(),
        DeviceStatusDiagnostic(),
        # Must be last, it depends on previous results
        PfDiagnostic()
    ]
    diagnostics_report = DiagnosticsReport(diagnostics)
    diagnostics_report.perform_diagnostics()
    LOGGER.debug("Full diagnostics report is: %s" % diagnostics_report)

    diagnostics_str = str(json.dumps(diagnostics_report))
    response_b64 = base64.b64encode(diagnostics_str.encode('ascii'))
    return response_b64


@DIAGNOSTICS.route('/robots.txt')
@cache.cached(timeout=60)
def noindex():
    robots = Response(response="User-Agent: *\nDisallow: /\n", status=200, mimetype="text/plain")
    robots.headers["Content-Type"] = "text/plain; charset=utf-8"
    return robots


@DIAGNOSTICS.route('/version')
@cache.cached(timeout=60)
def version_information():
    response = {
        'firmware_version': os.getenv('FIRMWARE_VERSION', 'unknown'),
        'diagnostics_version': os.getenv('DIAGNOSTICS_VERSION', 'unknown'),
        'firmware_short_hash': os.getenv('FIRMWARE_SHORT_HASH', 'unknown'),
    }

    return response


@DIAGNOSTICS.route('/v1/add-gateway-txn', methods=['POST'])
def add_gateway_txn():
    """
    Generates an add_gateway_txn if a destination name and wallets are defined and valid.
    Diagnostics report will be in the format below if successful.

    https://docs.helium.com/mine-hnt/full-hotspots/become-a-maker/hotspot-integration-testing/#generate-an-add-hotspot-transaction
    {
        errors: [],
        DESTINATION_ADD_GATEWAY_TXN_KEY: {
            "address": "11TL62V8NYvSTXmV5CZCjaucskvNR1Fdar1Pg4Hzmzk5tk2JBac",
            "fee": 65000,
            "owner": "14GWyFj9FjLHzoN3aX7Tq7PL6fEg4dfWPY8CrK8b9S5ZrcKDz6S",
            "payer": "138LbePH4r7hWPuTnK6HXVJ8ATM2QU71iVHzLTup1UbnPDvbxmr",
            "staking fee": 4000000,
            "txn": "CrkBCiEBrlImpYLbJ0z0hw5b4g9isRyPrgbXs9X+RrJ4pJJc9MkS..."
        }
    }
    """

    shipping_destination_with_signature = request.get_data()
    if not shipping_destination_with_signature:
        err_msg = 'Can not find payload.'
        LOGGER.error(err_msg)
        diagnostics_report = compose_diagnostics_report_from_err_msg(
            DESTINATION_ADD_GATEWAY_TXN_KEY, err_msg)
        return diagnostics_report, 406

    diagnostics = [
        AddGatewayTxnDiagnostic(GnuPG(), shipping_destination_with_signature),
    ]
    diagnostics_report = DiagnosticsReport(diagnostics)
    diagnostics_report.perform_diagnostics()
    if diagnostics_report.has_errors({DESTINATION_ADD_GATEWAY_TXN_KEY}):
        http_code = 500
    else:
        http_code = 200

    LOGGER.debug("add_gateway_txn result: %s" % diagnostics_report)

    return diagnostics_report, http_code


@DIAGNOSTICS.route('/v1/shutdown-gateway', methods=['POST'])
def shutdown_gateway():
    """
    Shuts down the gateway using the Balena supervisor API.
    Requires a signed PGP payload to be supplied in the format:

    -----BEGIN PGP SIGNED MESSAGE-----
    Hash: SHA256

    {
    "shutdown_gateway": true
    }
    -----BEGIN PGP SIGNATURE-----
    [REDACTED]
    -----END PGP SIGNATURE-----

    """

    shutdown_request_with_signature = request.get_data()
    if not shutdown_request_with_signature:
        err_msg = 'Can not find PGP payload.'
        LOGGER.error(err_msg)
        diagnostics_report = compose_diagnostics_report_from_err_msg(
            SHUTDOWN_GATEWAY_KEY, err_msg)
        return diagnostics_report, 406

    diagnostics = [
        ShutdownGatewayDiagnostic(GnuPG(), shutdown_request_with_signature),
    ]
    diagnostics_report = DiagnosticsReport(diagnostics)
    diagnostics_report.perform_diagnostics()
    if diagnostics_report.has_errors({SHUTDOWN_GATEWAY_KEY}):
        http_code = 500
    else:
        http_code = 200

    LOGGER.debug("shutdown_gateway result: %s" % diagnostics_report)

    return diagnostics_report, http_code


@DIAGNOSTICS.route('/v1/mfr-init', methods=['POST'])
def provision_key_view():
    """
    Tries key provisioning.
    Requires a signed PGP payload to be supplied in the format:

    -----BEGIN PGP SIGNED MESSAGE-----
    Hash: SHA256

    {
        "slot": int,
        "force": boolean
    }
    -----BEGIN PGP SIGNATURE-----
    [REDACTED]
    -----END PGP SIGNATURE-----

    :param slot: The slot number to use for key provisioning.
    :param force: If set to True then if "provision" operation fails, "key --generate" operation
                  is tried.
    :return: In case of success returns the provisioned json that include the onboarding key
             and animal name. In case of failure, returns the error message.
    """

    provision_request_with_signature = request.get_data()
    if not provision_request_with_signature:
        err_msg = 'Can not find PGP payload.'
        LOGGER.error(err_msg)
        diagnostics_report = compose_diagnostics_report_from_err_msg(
            SHUTDOWN_GATEWAY_KEY, err_msg)
        return diagnostics_report, 406

    diagnostics = [
        ProvisionKeyDiagnostic(GnuPG(), provision_request_with_signature),
    ]
    diagnostics_report = DiagnosticsReport(diagnostics)
    diagnostics_report.perform_diagnostics()
    if diagnostics_report.has_errors({SHUTDOWN_GATEWAY_KEY}):
        http_code = 500
    else:
        http_code = 200

    LOGGER.debug("shutdown_gateway result: %s" % diagnostics_report)

    return diagnostics_report, http_code


@DIAGNOSTICS.after_app_request
def add_security_headers(response):
    response.headers['X-Robots-Tag'] = 'none'

    return response
