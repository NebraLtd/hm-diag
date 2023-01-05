from sqlalchemy import Column
from sqlalchemy import String


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
