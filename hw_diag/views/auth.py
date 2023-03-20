import logging
import os
import datetime
import ipaddress

from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import session
from flask import jsonify
from hm_pyhelper.logger import get_logger

from hw_diag.utilities.diagnostics import read_diagnostics_file
from hw_diag.utilities.hardware import should_display_lte
from hw_diag.utilities.hardware import is_button_present
from hw_diag.utilities.auth import check_password
from hw_diag.utilities.auth import authenticate
from hw_diag.utilities.auth import update_password
from hw_diag.utilities.auth import count_recent_auth_failures
from hw_diag.utilities.auth import add_login_failure
from hw_diag.utilities.auth import update_password_reset_expiry
from hw_diag.utilities.auth import perform_password_reset
from hw_diag.utilities.auth import password_updated_in_last_minute
from hw_diag.utilities.auth import can_spawn_admin_session


logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

LOGGER = get_logger(__name__)
AUTH = Blueprint('AUTH', __name__)
LOGIN_FORM_TEMPLATE = 'login_form.html'

DOCKER_SUBNET = '172.17.0.0/16'


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
    color = result.get('color')
    diagnostics = read_diagnostics_file()
    now = datetime.datetime.utcnow()
    template_filename = 'password_change_form.html'

    return render_template(
        template_filename,
        diagnostics=diagnostics,
        display_lte=False,
        now=now,
        msg=msg,
        color=color
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
    button = is_button_present(diagnostics)

    return render_template(
        'password_reset.html',
        diagnostics=diagnostics,
        display_lte=display_lte,
        now=now,
        button=button
    )


@AUTH.route('/password_reset', methods=['POST'])
def handle_reset_password():
    # Check this originates from the docker private subnet, only
    # internal containers should be privileged to reset the password.
    request_ip = request.remote_addr
    if ipaddress.ip_address(request_ip) not in ipaddress.ip_network(DOCKER_SUBNET):
        return 'Unauthorised', 401

    password_reset = perform_password_reset()
    return jsonify({'password_updated': password_reset})


@AUTH.route('/password_reset', methods=['GET'])
def validate_password_reset():
    result = password_updated_in_last_minute()
    return jsonify({'password_updated': result})


@AUTH.route('/admin_session')
def spawn_admin_session():
    # This is used to allow Nebra support to log in remotely.
    # To log in the support must run the "start_admin_session"
    # command in the shell of the diagnostics container via
    # balena and then login via the balena public url feature
    # within 2 minutes of running the command.
    if not can_spawn_admin_session():
        return 'Unauthorized', 401

    referrer = request.headers.get('Host')
    if 'localhost' in referrer:
        session['logged_in'] = True
        return redirect('/')
    else:
        return 'Unauthorized', 401


@AUTH.route('/upgrade')
@authenticate
def display_upgrade_page():
    return render_template('upgrade.html')
