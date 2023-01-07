import logging
import os
import datetime

from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import session
from flask import jsonify
from hm_pyhelper.logger import get_logger

from hw_diag.utilities.diagnostics import read_diagnostics_file
from hw_diag.utilities.hardware import should_display_lte
from hw_diag.utilities.auth import check_password
from hw_diag.utilities.auth import authenticate
from hw_diag.utilities.auth import update_password
from hw_diag.utilities.auth import count_recent_auth_failures
from hw_diag.utilities.auth import add_login_failure
from hw_diag.utilities.auth import update_password_reset_expiry
from hw_diag.utilities.auth import perform_password_reset
from hw_diag.utilities.auth import password_updated_in_last_minute


logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

LOGGER = get_logger(__name__)
AUTH = Blueprint('AUTH', __name__)
LOGIN_FORM_TEMPLATE = 'login_form.html'


@AUTH.route('/login', methods=['GET'])
def get_login_form():
    diagnostics = read_diagnostics_file()
    display_lte = should_display_lte(diagnostics)
    now = datetime.datetime.utcnow()

    return render_template(
        LOGIN_FORM_TEMPLATE,
        diagnostics=diagnostics,
        display_lte=display_lte,
        now=now
    )


@AUTH.route('/change_password', methods=['GET'])
@authenticate
def get_password_change_form():
    diagnostics = read_diagnostics_file()
    now = datetime.datetime.utcnow()
    template_filename = 'password_change_form.html'

    return render_template(
        template_filename,
        diagnostics=diagnostics,
        display_lte=False,
        now=now
    )


@AUTH.route('/change_password', methods=['POST'])
@authenticate
def handle_password_change():
    current_password = request.form.get('txtOriginalPassword')
    new_password = request.form.get('txtNewPassword')
    confirm_password = request.form.get('txtConfirmPassword')

    result = update_password(
        current_password,
        new_password,
        confirm_password
    )

    msg = result.get('msg')
    diagnostics = read_diagnostics_file()
    now = datetime.datetime.utcnow()
    template_filename = 'password_change_form.html'

    return render_template(
        template_filename,
        diagnostics=diagnostics,
        display_lte=False,
        now=now,
        msg=msg
    )


@AUTH.route('/logout', methods=['GET'])
def handle_logout():
    session['logged_in'] = False
    diagnostics = read_diagnostics_file()
    display_lte = should_display_lte(diagnostics)
    now = datetime.datetime.utcnow()

    return render_template(
        LOGIN_FORM_TEMPLATE,
        diagnostics=diagnostics,
        display_lte=display_lte,
        now=now,
        msg='Logout Successful'
    )


@AUTH.route('/login', methods=['POST'])
def handle_login():
    if session.get('logged_in'):
        return redirect('/')

    diagnostics = read_diagnostics_file()
    display_lte = should_display_lte(diagnostics)
    now = datetime.datetime.utcnow()

    minutes = 10
    if count_recent_auth_failures(minutes=minutes) > 4:
        return render_template(
            LOGIN_FORM_TEMPLATE,
            diagnostics=diagnostics,
            display_lte=display_lte,
            now=now,
            msg=('Login locked due to too many login failures. Please '
                 'wait %s minutes and try again.' % minutes)
        )

    password = request.form.get('txtPassword')
    if check_password(password):
        session['logged_in'] = True
        return redirect('/')
    else:
        add_login_failure(request.remote_addr)

    return render_template(
        LOGIN_FORM_TEMPLATE,
        diagnostics=diagnostics,
        display_lte=display_lte,
        now=now,
        msg='Incorrect password. Please try again!'
    )


@AUTH.route('/reset_password')
def display_password_reset_page():
    if session.get('logged_in'):
        return redirect('/')

    diagnostics = read_diagnostics_file()
    display_lte = should_display_lte(diagnostics)
    now = datetime.datetime.utcnow()

    update_password_reset_expiry()

    return render_template(
        'password_reset.html',
        diagnostics=diagnostics,
        display_lte=display_lte,
        now=now
    )


@AUTH.route('/password_reset', methods=['POST'])
def handle_reset_password():
    # Check this originates from the docker private subnet, only
    # internal containers should be privileged to reset the password.
    password_reset = perform_password_reset()
    return jsonify({'password_updated': password_reset})


@AUTH.route('/password_reset', methods=['GET'])
def validate_password_reset():
    result = password_updated_in_last_minute()
    return jsonify({'password_updated': result})
