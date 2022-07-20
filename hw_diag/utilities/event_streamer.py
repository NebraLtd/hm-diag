from enum import Enum, auto
import os
import requests
import logging
from persistqueue import Queue

from hw_diag.utilities import system_metrics
from hw_diag.utilities.events_bq_data_model import EventDataModel

log = logging.getLogger()
log.setLevel(logging.DEBUG)

VOLUME_PATH = '/var/watchdog/events'

NETWORK_EVENT_BASE = 0
CONTAINER_EVENT_BASE = 1000

NETWORK_ACTION_BASE = 10000
CONTAINER_ACTION_BASE = 11000


class DiagEvent(Enum):
    NETWORK_DISCONNECTED = NETWORK_ACTION_BASE  # completely disconnected.
    NETWORK_LOCAL_CONNECTED = auto()  # connected to local gateway
    NETWORK_INTERNET_CONNECTED = auto()  # connected to internet


class DiagAction(Enum):
    ACTION_NONE = -1
    ACTION_NM_RESTART = NETWORK_ACTION_BASE
    ACTION_SYSTEM_REBOOT = auto()
    ACTION_SYSTEM_REBOOT_FORCED = auto()


BUCKET_NAME = os.getenv(
    'MINER_EVENTS_GCS_BUCKET',
    'helium-miner-events'
)

URL = 'https://www.googleapis.com/upload/storage/v1/b/%s/o?uploadType=media' \
    % BUCKET_NAME


event_queue = Queue(VOLUME_PATH, maxsize=1000)
EVENT_TYPE_KEY = 'event_type'
ACTION_TYPE_KEY = 'action_type'


def event_fingerprint(event_type, action_type=DiagAction.ACTION_NONE, msg="") -> str:
    # right now event fingerprint is decided base on only these three"
    fingerprint = f"{event_type}_{action_type}_{msg}"
    return fingerprint[:128]


def enqueue_event(event):
    event_queue.put(event)
    process_queued_events()


def process_queued_events():
    while not event_queue.empty():
        event = event_queue.get()
        if not _upload_event(event):
            return
        event_queue.task_done()


def _upload_event(event: dict) -> bool:

    # add serial number to filename to prevent overwriting
    cloud_filename = f'{system_metrics.get_serial_number()}-{event["generated_ts"]}.json'

    # enqueue only if it passes the big query data model
    try:
        # validate and filter diagnostic data as per big query model
        validated_data = EventDataModel(**event)
    except Exception as err:
        log.error(f'Failed to enforce biquery data model on diagnostics dict {err}')
        return False

    upload_url = '%s&name=%s' % (URL, cloud_filename)
    headers = {'Content-Type': 'application/json'}
    content = validated_data.json()

    print(f"uploading event: {content}")

    try:
        resp = requests.post(upload_url, headers=headers, data=content)

        if resp.status_code != 200:
            log.error(
                'Error submitting event to GCS bucket: %s - %s'
                % (resp.status_code, resp.text)
            )
            return False
    except Exception as err:
        log.error('Error submitting event to GCS bucket: %s' % str(err))
        return False

    log.debug('event Submitted to GCS Bucket Successfully')
    return True
