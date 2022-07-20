from enum import Enum, auto
import os
import json
import requests
import logging


from hw_diag.utilities import system_metrics
from hw_diag.utilities.events_bq_data_model import EventDataModel
from hw_diag.utilities.osutils import get_rw_storage_path
from hw_diag.utilities.fifo_disk_queue import FifoDiskQueue

log = logging.getLogger()
log.setLevel(logging.DEBUG)

VOLUME_PATH = '/var/watchdog'
EVENTS_FOLDER = 'events'

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


event_queue = FifoDiskQueue(get_rw_storage_path(VOLUME_PATH, EVENTS_FOLDER), maxsize=1000)
EVENT_TYPE_KEY = 'event_type'
ACTION_TYPE_KEY = 'action_type'


def event_fingerprint(event_type, action_type=DiagAction.ACTION_NONE, msg="") -> str:
    # right now event fingerprint is decided base on only these three"
    fingerprint = f"{event_type}_{action_type}_{msg}"
    return fingerprint[:128]


def enqueue_event(event) -> None:
    try:
        EventDataModel(**event)
    except Exception as e:
        logging.error(f"failed to enforce bigquery datamodel, modify schema or event to fix: {e}")
        return

    event_queue.put(event)

    # if process events throws exception, empty the queue to recover
    try:
        process_queued_events()
    except Exception as e:
        logging.error(f"emptying queue due to corruption: {e}")
        empty_queued_events()


def empty_queued_events():
    while not event_queue.empty():
        event_queue.get()
        event_queue.task_done()


def process_queued_events():
    while not event_queue.empty():
        # we don't need to worry about get blocking as we are not working with
        # threads here.
        event = event_queue.peek()
        if not _upload_event(event):
            return
        # remove the event from the queue
        event_queue.get()
        event_queue.task_done()


def _upload_event(event: dict) -> bool:
    '''returns false if network request fails'''

    # add serial number to filename to prevent overwriting
    cloud_filename = f'{system_metrics.get_serial_number()}-{event["generated_ts"]}.json'

    upload_url = '%s&name=%s' % (URL, cloud_filename)
    headers = {'Content-Type': 'application/json'}
    content = json.dumps(event)

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
