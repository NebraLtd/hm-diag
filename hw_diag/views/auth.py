import logging
import os
import datetime

from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import session
from hm_pyhelper.logger import get_logger

from hw_diag.utilities.diagnostics import read_diagnostics_file
from hw_diag.utilities.hardware import should_display_lte
from hw_diag.utilities.auth import check_password
from hw_diag.utilities.auth import authenticate


logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"))

LOGGER = get_logger(__name__)
AUTH = Blueprint('AUTH', __name__)


@AUTH.route('/login', methods=['GET'])
def get_login_form():
    diagnostics = read_diagnostics_file()
    display_lte = should_display_lte(diagnostics)
    now = datetime.datetime.utcnow()
    template_filename = 'login_form.html'

    return render_template(
        template_filename,
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


@AUTH.route('/logout', methods=['GET'])
def handle_logout():
    session['logged_in'] = False
    diagnostics = read_diagnostics_file()
    display_lte = should_display_lte(diagnostics)
    now = datetime.datetime.utcnow()
    template_filename = 'login_form.html'

    return render_template(
        template_filename,
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
    template_filename = 'login_form.html'

    password = request.form.get('txtPassword')
    if check_password(password):
        session['logged_in'] = True
        return redirect('/')

    return render_template(
        template_filename,
        diagnostics=diagnostics,
        display_lte=display_lte,
        now=now,
        msg='Incorrect password. Please try again!'
    )
