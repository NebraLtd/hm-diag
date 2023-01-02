import logging
import os
import datetime

from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import session
from password_strength import PasswordPolicy
from hm_pyhelper.logger import get_logger

from hw_diag.utilities.diagnostics import read_diagnostics_file
from hw_diag.utilities.hardware import should_display_lte
from hw_diag.utilities.auth import check_password
from hw_diag.utilities.auth import authenticate
from hw_diag.utilities.auth import write_password_file


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
    error = False
    msg = ''
    current_password = request.form.get('txtOriginalPassword')
    new_password = request.form.get('txtNewPassword')
    confirm_password = request.form.get('txtConfirmPassword')

    if not check_password(current_password):
        error = True
        msg = 'Current password is not valid.'

    if new_password != confirm_password:
        error = True
        msg = 'New password and password confirmation do not match.'

    policy = PasswordPolicy.from_names(
        length=8,  # min length: 8
        uppercase=1,  # need min. 2 uppercase letters
        numbers=1,  # need min. 2 digits
        special=1,  # need min. 2 special characters
        nonletters=0,  # need min. 2 non-letter characters (digits, specials, anything)
    )

    if len(policy.test(new_password)) > 0:
        error = True
        msg = (
            'Password is not complex enough, please ensure password is greater than 8 '
            'characters, has atleast 1 number, 1 uppercase character and 1 special character.'
        )

    if not error:
        write_password_file(new_password)
        msg = 'Password updated successfully.'

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

    password = request.form.get('txtPassword')
    if check_password(password):
        session['logged_in'] = True
        return redirect('/')

    return render_template(
        LOGIN_FORM_TEMPLATE,
        diagnostics=diagnostics,
        display_lte=display_lte,
        now=now,
        msg='Incorrect password. Please try again!'
    )
