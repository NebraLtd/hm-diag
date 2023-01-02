import json
import bcrypt

from functools import wraps
from flask import redirect
from flask import session

from hw_diag.utilities.diagnostics import read_diagnostics_file


AUTH_FILE = '/var/data/auth.json'


def authenticate(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect('/login')
        return f(*args, **kwargs)
    return wrapper


def write_password_file(password):
    password = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    hashed_str = hashed.decode('utf-8')
    auth_data = {
        'pw_hash': hashed_str
    }
    with open(AUTH_FILE, 'w') as f:
        json.dump(auth_data, f)
    return auth_data


def read_password_file():
    auth_data = None
    try:
        with open(AUTH_FILE, 'r') as f:
            auth_data = json.load(f)
    except FileNotFoundError:
        diagnostics = read_diagnostics_file()
        eth_mac = diagnostics.get('E0')
        default_password = eth_mac.replace(':', '')
        auth_data = write_password_file(default_password)
    return auth_data


def check_password(password):
    auth_data = read_password_file()
    hashed_password = auth_data.get('pw_hash').encode('utf-8')
    password = password.encode('utf-8')
    if bcrypt.checkpw(password, hashed_password):
        return True
    else:
        return False
