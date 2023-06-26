import logging
import os
import shutil

from flask import Blueprint
from flask import render_template
from flask import redirect
from flask import request

from hm_pyhelper.logger import get_logger
from hw_diag.utilities.auth import authenticate
from hw_diag.utilities.auth import commercial_fleet_only
from hw_diag.utilities.db import get_value
from hw_diag.utilities.db import set_value
from hw_diag.utilities.thix import get_unknown_gateways
from hw_diag.utilities.thix import get_gateways
from hw_diag.utilities.thix import submit_onboard
from hw_diag.utilities.thix import remove_testnet
from hw_diag.utilities.thix import is_region_set
from hw_diag.utilities.thix import write_region_file
from hw_diag.utilities.diagnostics import read_diagnostics_file


logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

LOGGER = get_logger(__name__)
THINGSIX = Blueprint('THINGSIX', __name__)

THINGSIX_ONBOARD_URL = 'https://app.thingsix.com/gateways/onboarding?gatewayId=%s'
THINGSIX_CONFIG_TEMPLATE = '/opt/thingsix/thingsix_config.yaml'
THINGSIX_CONFIG_FILE = '/var/thix/config.yaml'
THINGSIX_SETUP_TEMPLATE = 'thix_setup.html'
THINGSIX_ONBOARD_TEMPLATE = 'thix_onboard.html'
THINGSIX_SET_REGION_TEMPLATE = 'thix_set_region.html'

REGION_PREFIXES = (
    'AS923',
    'AU915',
    'CN470',
    'EU433',
    'EU868',
    'IN865',
    'KR920',
    'RU864',
    'US915'
)

@THINGSIX.route('/thingsix')
@authenticate
@commercial_fleet_only
def get_thix_dashboard():
    # If THIX isn't enabled render the setup page.
    diagnostics = read_diagnostics_file()

    try:
        if get_value('thix_enabled') != 'true':
            raise Exception("ThingsIX not enabled yet.")
    except Exception:
        # Check if region is set, if not set then send user to the set region page...
        if not is_region_set():
            return render_template(THINGSIX_SET_REGION_TEMPLATE, diagnostics=diagnostics)
        return render_template(THINGSIX_SETUP_TEMPLATE, diagnostics=diagnostics)

    try:
        if get_value('thix_onboarded') == 'true':
            # Here we must undo the previous testnet stuff...
            remove_testnet()
            set_value('thix_enabled', 'false')
            set_value('thix_onboarded', 'false')
            return render_template(THINGSIX_SETUP_TEMPLATE, diagnostics=diagnostics)
    except Exception:  # nosec
        pass

    # If THIX is enabled but isn't onboarded render the onboard page.
    try:
        if get_value('thix_onboarded') != 'mainnet':
            render_template(THINGSIX_ONBOARD_TEMPLATE, diagnostics=diagnostics)
    except Exception:
        return render_template(THINGSIX_ONBOARD_TEMPLATE, diagnostics=diagnostics)

    try:
        gateways = get_gateways()
        gateway = gateways.get('onboarded')[0]

        # Else just render the THIX dashboard.
        return render_template(
            'thix_dashboard.html',
            gateway=gateway,
            diagnostics=diagnostics
        )

    except Exception:  # nosec
        return render_template(
            'thix_error.html',
            diagnostics=diagnostics
        )


@THINGSIX.route('/thingsix/enable')
@authenticate
@commercial_fleet_only
def enable_thix():
    # Only allow this if it's currently not enabled...
    try:
        if get_value('thix_enabled') == 'true':
            return 'ThingsIX already enabled', 400
    except Exception:  # nosec
        pass

    # Copy the config into place...
    shutil.copy(THINGSIX_CONFIG_TEMPLATE, THINGSIX_CONFIG_FILE)
    set_value('thix_enabled', 'true')
    return 'Accepted', 202


@THINGSIX.route('/thingsix/set_region', methods=['POST'])
@authenticate
@commercial_fleet_only
def set_region():
    region = request.form.get('selRegion')

    # Validate region is valid...
    if not region.startswith(REGION_PREFIXES):
        return 'Bad region provided', 400

    # Set the region file and redirect user back to the onboard...
    write_region_file(region)
    return redirect('/thingsix')


@THINGSIX.route('/thingsix/onboard', methods=['POST'])
@authenticate
@commercial_fleet_only
def process_onboard():  # noqa:C901
    diagnostics = read_diagnostics_file()
    # Only allow this if it's currently enabled and not onboarded...
    try:
        if get_value('thix_enabled') != 'true':
            return render_template(
                THINGSIX_ONBOARD_TEMPLATE,
                diagnostics=diagnostics,
                msg='ThingsIX gateway needs to be enabled before onboarding!'
            )
    except Exception:  # nosec
        pass

    try:
        if get_value('thix_onboarded') == 'true':
            return render_template(
                THINGSIX_ONBOARD_TEMPLATE,
                diagnostics=diagnostics,
                msg='ThingsIX gateway already onboarded!'
            )
    except Exception:  # nosec
        pass

    gateways = get_unknown_gateways()
    try:
        gateway = gateways[0].get('localId')
    except IndexError:
        # Probably already registered but not yet onboarded... Fetch from
        # known gateways list.
        gateways = get_gateways()
        pending_gateways = gateways.get('pending')
        gateway = pending_gateways[0].get('localId')

    logging.info('Gateway to onboard: %s' % gateway)

    try:
        # We should probably validate this and return error if it's wrong.
        wallet = request.form.get('txtWalletId')
        logging.info('Onboarding wallet: %s' % wallet)

        onboard = submit_onboard(gateway, wallet)
    except Exception as err:
        return render_template(
            THINGSIX_ONBOARD_TEMPLATE,
            diagnostics=diagnostics,
            msg=('Error occured during onboard. '
                 'Please check wallet id and try again - %s'
                 % str(err))
        )

    gateway_id = onboard.get('gatewayId')
    set_value('thix_onboarded', 'mainnet')
    return redirect(THINGSIX_ONBOARD_URL % gateway_id)
