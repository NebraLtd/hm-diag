from flask import g
from sqlalchemy.exc import NoResultFound

from hw_diag.database.models.auth import AuthKeyValue


def get_value(key, default=None):
    try:
        row = g.db.query(AuthKeyValue). \
            filter(AuthKeyValue.key == key). \
            one()
        return row.value
    except NoResultFound:
        if default:
            return default
        raise Exception("No value found for key %s" % key)


def set_value(key, value):
    try:
        kv_pair = g.db.query(AuthKeyValue). \
            filter(AuthKeyValue.key == key). \
            one()
        kv_pair.value = value
        g.db.commit()
    except NoResultFound:
        kv_pair = AuthKeyValue(
            key=key,
            value=value
        )
        g.db.add(kv_pair)
        g.db.commit()

    return kv_pair
