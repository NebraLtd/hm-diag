import logging
import os
import time
import json

from flask import Blueprint
from flask import render_template
from flask import request

from hm_pyhelper.logger import get_logger
from hw_diag.utilities.auth import authenticate
from hw_diag.utilities.auth import commercial_fleet_only
from hw_diag.utilities.balena_supervisor import BalenaSupervisor
from hw_diag.utilities.diagnostics import read_diagnostics_file
from hw_diag.utilities.dashboard_registration import claim_miner_deeplink
from hw_diag.utilities.sdr import detect_sdr


logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

LOGGER = get_logger(__name__)
WINGBITS = Blueprint('WINGBITS', __name__)

WINGBITS_CONFIG_FILE = '/var/nebra/wingbits.json'


def get_or_create_wingbits_config():
    data = None
    try:
        with open(WINGBITS_CONFIG_FILE, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {
            "node_name": "name-not-set",
            "latitude": 0.0,
            "longitude": 0.0
        }
        with open(WINGBITS_CONFIG_FILE, 'w') as f:
            json.dump(data, f)
    return data


def write_wingbits_config(data):
    with open(WINGBITS_CONFIG_FILE, 'w') as f:
        json.dump(data, f)


@WINGBITS.route('/wingbits')
@authenticate
@commercial_fleet_only
def get_wingbits_dashboard():
    diagnostics = read_diagnostics_file()
    claim_deeplink = claim_miner_deeplink()
    now = round(time.time())
    sdr_present = detect_sdr()
    config = get_or_create_wingbits_config()

    return render_template(
        'wingbits.html',
        diagnostics=diagnostics,
        claim_deeplink=claim_deeplink,
        sdr_present=sdr_present,
        config=config,
        now=now
    )


@WINGBITS.route('/wingbits/tar1090')
@authenticate
@commercial_fleet_only
def get_wingbits_tar1090():
    diagnostics = read_diagnostics_file()
    claim_deeplink = claim_miner_deeplink()
    now = round(time.time())

    return render_template(
        'wingbits_tar1090.html',
        diagnostics=diagnostics,
        claim_deeplink=claim_deeplink,
        now=now
    )


@WINGBITS.route('/wingbits/graphs1090')
@authenticate
@commercial_fleet_only
def get_wingbits_graphs1090():
    diagnostics = read_diagnostics_file()
    claim_deeplink = claim_miner_deeplink()
    now = round(time.time())

    return render_template(
        'wingbits_graph1090.html',
        diagnostics=diagnostics,
        claim_deeplink=claim_deeplink,
        now=now
    )


@WINGBITS.route('/wingbits', methods=['POST'])
@authenticate
@commercial_fleet_only
def update_wingbits_config():
    diagnostics = read_diagnostics_file()
    claim_deeplink = claim_miner_deeplink()
    now = round(time.time())

    try:
        config = {
            "node_name": request.form.get('txtNodeName'),
            "longitude": float(request.form.get('txtLongitude')),
            "latitude": float(request.form.get('txtLatitude'))
        }
    except Exception as err:
        logging.error("Error updating wingbits config: %s" % str(err))
        config = get_or_create_wingbits_config()
        sdr_present = detect_sdr()

        return render_template(
            'wingbits.html',
            diagnostics=diagnostics,
            claim_deeplink=claim_deeplink,
            sdr_present=sdr_present,
            config=config,
            now=now,
            error="Invalid configuration options."
        )

    write_wingbits_config(config)

    supervisor = BalenaSupervisor.new_from_env()
    supervisor.reboot()

    return render_template(
        'reconfigure_countdown.html',
        seconds=120,
        next_url='/',
        diagnostics=diagnostics,
        claim_deeplink=claim_deeplink,
        now=now
    )
