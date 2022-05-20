from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class DiagnosticDataModel(BaseModel):
    last_updated_ts: datetime
    last_updated: str
    E0: Optional[str]
    W0: Optional[str]
    BN: str
    ID: str
    BA: str
    FR: str
    FW: str
    VA: str
    serial_number: str
    ECC: Optional[bool]
    LOR: Optional[bool]
    PK: str
    OK: str
    AN: str
    MC: Optional[bool]
    MD: Optional[bool]
    MH: Optional[int]
    MN: Optional[str]
    MR: Optional[bool]
    BCH: Optional[int]
    MS: Optional[bool]
    BSP: Optional[float]
    BT: Optional[bool]
    LTE: Optional[bool]
    RE: Optional[str]
    PF: Optional[bool]
    FRIENDLY: Optional[str]
    APPNAME: Optional[str]
    SPIBUS: Optional[str]
    RESET: Optional[int]
    MAC: Optional[str]
    STATUS: Optional[int]
    BUTTON: Optional[int]
    ECCOB: Optional[bool]
    TYPE: Optional[str]
    CELLULAR: Optional[bool]
    uptime_seconds: Optional[int]
    firmware_short_hash: Optional[str]
