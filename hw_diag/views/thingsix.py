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


logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

LOGGER = get_logger(__name__)
THINGSIX = Blueprint('THINGSIX', __name__)

THINGSIX_ONBOARD_URL = 'https://app-testnet.thingsix.com/gateways/onboarding?gatewayId=%s'
THINGSIX_CONFIG_TEMPLATE = '/opt/thingsix/thingsix_config.yaml'
THINGSIX_CONFIG_FILE = '/var/thix/config.yaml'


@THINGSIX.route('/thingsix')
@authenticate
@commercial_fleet_only
def get_thix_dashboard():
    # If THIX isn't enabled render the setup page.
    try:
        if get_value('thix_enabled') != 'true':
            render_template('thix_setup.html')
    except Exception:
        return render_template('thix_setup.html')

    # If THIX is enabled but isn't onboarded render the onboard page.
    try:
        if get_value('thix_onboarded') != 'true':
            render_template('thix_onboard.html')
    except Exception:
        return render_template('thix_onboard.html')

    gateways = get_gateways()
    gateway = gateways.get('onboarded')[0]

    # Else just render the THIX dashboard.
    return render_template(
        'thix_dashboard.html',
        gateway=gateway
    )


@THINGSIX.route('/thingsix/enable')
@authenticate
@commercial_fleet_only
def enable_thix():
    # Only allow this if it's currently not enabled...
    try:
        if get_value('thix_enabled') == 'true':
            return 'ThingsIX already enabled', 400
    except Exception:
        pass

    # Copy the config into place...
    shutil.copy(THINGSIX_CONFIG_TEMPLATE, THINGSIX_CONFIG_FILE)
    set_value('thix_enabled', 'true')
    return 'Accepted', 202


@THINGSIX.route('/thingsix/onboard', methods=['POST'])
@authenticate
@commercial_fleet_only
def process_onboard():
    # Only allow this if it's currently enabled and not onboarded...
    try:
        if get_value('thix_enabled') != 'true':
            return render_template(
                'thix_onboard.html',
                msg='ThingsIX gateway needs to be enabled before onboarding!'
            )
    except Exception:
        pass

    try:
        if get_value('thix_onboarded') == 'true':
            return render_template(
                'thix_onboard.html',
                msg='ThingsIX gateway already onboarded!'
            )
    except Exception:
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
            'thix_onboard.html',
            msg=('Error occured during onboard. '
                 'Please check wallet id and try again - %s'
                 % str(err))
        )

    gateway_id = onboard.get('gatewayId')
    set_value('thix_onboarded', 'true')
    return redirect(THINGSIX_ONBOARD_URL % gateway_id)
