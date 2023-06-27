import logging
import os

from flask import Blueprint
from flask import render_template
from flask import send_file
from flask import request

from hm_pyhelper.logger import get_logger
from hw_diag.utilities.auth import authenticate
from hw_diag.utilities.backup import perform_backup
from hw_diag.utilities.backup import perform_restore
from hw_diag.utilities.backup import update_backup_checkpoint
from hw_diag.utilities.balena_supervisor import BalenaSupervisor
from hw_diag.utilities.diagnostics import read_diagnostics_file


logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

LOGGER = get_logger(__name__)
BACKUP_RESTORE = Blueprint('BACKUP_RESTORE', __name__)


@BACKUP_RESTORE.route('/backup_restore')
@authenticate
def get_backup_page():
    diagnostics = read_diagnostics_file()
    claim_deeplink = claim_miner_deeplink()
    
    return render_template(
        'backup_restore.html', 
        diagnostics=diagnostics,
        claim_deeplink=claim_deeplink
    )


@BACKUP_RESTORE.route('/backup')
@authenticate
def do_backup():
    backup_file = perform_backup()
    update_backup_checkpoint()
    return send_file(backup_file, as_attachment=True)


@BACKUP_RESTORE.route('/restore', methods=['POST'])
@authenticate
def do_restore():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        uploaded_file.save('/tmp/restore.tar')  # nosec
    else:
        return "Bad Request: Invalid backup file", 400
    try:
        perform_restore()
        update_backup_checkpoint()
        supervisor = BalenaSupervisor.new_from_env()
        supervisor.reboot()

        return render_template(
            'reconfigure_countdown.html',
            seconds=120,
            next_url='/'
        )
    except Exception:
        return 'Error during restoration', 500
