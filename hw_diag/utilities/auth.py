import datetime
import bcrypt

from functools import wraps
from flask import redirect
from flask import session
from flask import g
from sqlalchemy.exc import NoResultFound
from password_strength import PasswordPolicy

from hw_diag.utilities.diagnostics import read_diagnostics_file
from hw_diag.database.models.auth import AuthKeyValue
from hw_diag.database.models.auth import AuthFailure


AUTH_FILE = '/var/data/auth.json'


def authenticate(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect('/login')
        return f(*args, **kwargs)
    return wrapper


def write_password(password):
    password = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password, salt)
    hashed_str = hashed.decode('utf-8')

    try:
        password_row = g.db.query(AuthKeyValue). \
            filter(AuthKeyValue.key == 'password_hash'). \
            one()
        password_row.value = hashed_str
    except NoResultFound:
        password_row = AuthKeyValue(
            key='password_hash',
            value=hashed_str
        )
        g.db.add(password_row)
    g.db.commit()

    return password_row


def read_password():
    try:
        password_row = g.db.query(AuthKeyValue). \
            filter(AuthKeyValue.key == 'password_hash'). \
            one()
    except NoResultFound:
        diagnostics = read_diagnostics_file()
        eth_mac = diagnostics.get('E0')
        default_password = eth_mac.replace(':', '')
        password_row = write_password(default_password)
    return password_row


def check_password(password):
    password_row = read_password()
    hashed_password = password_row.value.encode('utf-8')
    password = password.encode('utf-8')
    if bcrypt.checkpw(password, hashed_password):
        return True
    else:
        return False


def update_password(current_password, new_password, confirm_password):
    error = False
    msg = ''

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
        write_password(new_password)
        msg = 'Password updated successfully.'

    return {
        'error': error,
        'msg': msg
    }


def count_recent_auth_failures(minutes=10):
    now = datetime.datetime.utcnow()
    dt = now - datetime.timedelta(minutes=minutes)
    failure_count = g.db.query(AuthFailure). \
        filter(AuthFailure.dt > dt). \
        count()
    return failure_count


def add_login_failure(ip):
    now = datetime.datetime.utcnow()
    auth_failure = AuthFailure(
        dt=now,
        ip=ip
    )
    g.db.add(auth_failure)
    g.db.commit()


def update_password_reset_expiry():
    now = datetime.datetime.utcnow()
    expiry = now + datetime.timedelta(minutes=1)

    try:
        reset_expiry_row = g.db.query(AuthKeyValue). \
            filter(AuthKeyValue.key == 'password_reset_expiry'). \
            one()
        reset_expiry_row.value = expiry.isoformat()
        g.db.commit()
    except NoResultFound:
        reset_expiry_row = AuthKeyValue(
            key='password_reset_expiry',
            value=expiry.isoformat()
        )
        g.db.add(reset_expiry_row)
        g.db.commit()


def check_password_reset_expiry():
    now = datetime.datetime.utcnow()
    expiry = now + datetime.timedelta(minutes=1)

    try:
        reset_expiry_row = g.db.query(AuthKeyValue). \
            filter(AuthKeyValue.key == 'password_reset_expiry'). \
            one()
        reset_expiry_row.value = expiry.isoformat()
        g.db.commit()
    except NoResultFound:
        reset_expiry_row = AuthKeyValue(
            key='password_reset_expiry',
            value=expiry.isoformat()
        )
        g.db.add(reset_expiry_row)
        g.db.commit()

    return expiry
