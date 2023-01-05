from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy import DateTime


from hw_diag.database import BASE


class AuthKeyValue(BASE):
    __tablename__ = 'auth_kv'

    key = Column(
        String(60),
        nullable=False,
        primary_key=True
    )
    value = Column(
        String(250),
        nullable=False
    )


class AuthFailure(BASE):
    __tablename__ = 'auth_failures'

    dt = Column(
        DateTime(),
        nullable=False,
        primary_key=True
    )
    ip = Column(
        String(45),
        nullable=True
    )
