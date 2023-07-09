from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class DiagnosticDataModel(BaseModel):
    last_updated_ts: datetime
    last_updated: str
    E0: Optional[str] = None
    W0: Optional[str] = None
    BN: Optional[str] = None
    ID: Optional[str] = None
    BA: Optional[str] = None
    FR: Optional[str] = None
    FW: Optional[str] = None
    VA: Optional[str] = None
    serial_number: Optional[str] = None
    ECC: Optional[bool] = None
    LOR: Optional[bool] = None
    PK: Optional[str] = None
    OK: Optional[str] = None
    AN: Optional[str] = None
    MC: Optional[bool] = None
    MD: Optional[bool] = None
    MH: Optional[int] = None
    MN: Optional[str] = None
    MR: Optional[bool] = None
    BCH: Optional[int] = None
    MS: Optional[bool] = None
    BSP: Optional[float] = None
    BT: Optional[bool] = None
    LTE: Optional[bool] = None
    RE: Optional[str] = None
    PF: Optional[bool] = None
    FRIENDLY: Optional[str] = None
    APPNAME: Optional[str] = None
    SPIBUS: Optional[str] = None
    RESET: Optional[int] = None
    MAC: Optional[str] = None
    STATUS: Optional[int] = None
    BUTTON: Optional[int] = None
    ECCOB: Optional[bool] = None
    TYPE: Optional[str] = None
    CELLULAR: Optional[bool] = None
    uptime_seconds: Optional[int] = None
    firmware_short_hash: Optional[str] = None
