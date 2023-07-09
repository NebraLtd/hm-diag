from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List


class EventDataModel(BaseModel):
    generated_ts: datetime
    event_type: Optional[str] = None
    serial: Optional[str] = None
    variant: Optional[str] = None
    firmware_version: Optional[str] = None
    region_override: Optional[str] = None
    packet_errors: Optional[int] = None
    msg: Optional[str] = None
    action_type: Optional[str] = None
    uptime_hours: Optional[float] = None
    balena_app_state: Optional[str] = None
    balena_release: Optional[str] = None
    balena_all_running: Optional[bool] = None
    balena_failed_containers: List[str]
    balena_api_status: Optional[str] = None
    network_state: Optional[str] = None
