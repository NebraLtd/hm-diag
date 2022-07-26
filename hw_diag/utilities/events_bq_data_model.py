from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List


class EventDataModel(BaseModel):
    generated_ts: datetime
    event_type: Optional[str]
    serial: Optional[str]
    variant: Optional[str]
    firmware_version: Optional[str]
    region_override: Optional[str]
    packet_errors: Optional[int]
    msg: Optional[str]
    action_type: Optional[str]
    uptime_hours: Optional[float]
    balena_app_state: Optional[str]
    balena_release: Optional[str]
    balena_all_running: Optional[bool]
    balena_failed_containers: List[str]
    balena_api_status: Optional[str]
