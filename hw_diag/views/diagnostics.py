import json
import base64

from flask import Blueprint
from flask import render_template
from flask import request
from flask import jsonify

from jsonrpcclient import request as rpcrequest

from hw_diag.utilities.hardware import should_display_lte


DIAGNOSTICS = Blueprint('DIAGNOSTICS', __name__)


def read_diagnostics_file():
    diagnostics = {}
    try:
        with open('diagnostic_data.json', 'r') as f:
            diagnostics = json.load(f)
    except FileNotFoundError:
        msg = 'Diagnostics have not yet run, please try again in a few minutes'
        diagnostics = {'error': msg}
    return diagnostics


@DIAGNOSTICS.route('/')
def get_diagnostics():
    diagnostics = read_diagnostics_file()

    if request.args.get('json'):
        response = jsonify(diagnostics)
        response.headers.set('Content-Disposition',
                             'attachment;filename=nebra-diag.json'
                             )
        return response

    display_lte = should_display_lte(diagnostics)

    return render_template(
        'diagnostics_page.html',
        diagnostics=diagnostics,
        display_lte=display_lte
    )


@DIAGNOSTICS.route('/jsonrpc')
def check_jsonrpc_alive():
    JSONRPC_URL = 'http://helium-miner:4467'
    response = rpcrequest(JSONRPC_URL, 'info_summary')
    return jsonify(response.data.result)


@DIAGNOSTICS.route('/initFile.txt')
def get_initialisation_file():
    diagnostics = read_diagnostics_file()

    if diagnostics.get('error'):
        return 'Internal Server Error', 500

    response = {
        "VA": diagnostics['VA'],
        "FR": diagnostics['FR'],
        "E0": diagnostics['E0'],
        "RPI": diagnostics['RPI'],
        "OK": diagnostics['OK'],
        "PK": diagnostics['PK'],
        "PF": diagnostics["PF"],
        "ID": diagnostics["ID"]
    }

    response_b64 = base64.b64encode(str(json.dumps(response)).encode('ascii'))
    return response_b64
