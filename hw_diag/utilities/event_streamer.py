from datetime import datetime
from enum import Enum, auto
import json
import os
import requests
import logging

from hw_diag.utilities import system_metrics
from hw_diag.utilities.events_bq_data_model import EventDataModel

log = logging.getLogger()
log.setLevel(logging.DEBUG)

VOLUME_PATH = '/var/watchdog/'

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


event_queue = {}
EVENT_TYPE_KEY = 'event_type'
ACTION_TYPE_KEY = 'action_type'


def event_fingerprint(event_type, action_type=DiagAction.ACTION_NONE, msg=""):
    # right now event fingerprint is decided base on only these three"
    return f"{event_type}_{action_type}_{msg}"


def enqueue_event(event):
    event_queue[datetime.now()] = event
    process_queued_events()


def process_queued_events():
    _process_disk_queue()
    _process_mem_queue()
    # if uploads are failing for some reason, we need to write to disk
    _write_queue_to_disk()


def _json_filename(timestamp):
    return f"{timestamp}.json"  # using default iso format


def _process_mem_queue():
    # upload in chronological order and remove from queue
    for timestamp in sorted(event_queue.keys()):
        if not _upload_event(event_queue[timestamp], _json_filename(timestamp)):
            return False
        event_queue.pop(timestamp)
    return True


def _process_disk_queue():
    storage_path = os.path.join(VOLUME_PATH, 'events')

    # create a map { timestamp: eventfile }, we use this timestamp for sorting and uploading
    date_to_filename = {}
    for file in os.listdir(storage_path):
        if file.endswith('.json'):
            date_to_filename[(datetime.fromisoformat(file.split('.')[0]))] = file

    # upload by timestamp
    for timestamp in sorted(date_to_filename.keys()):
        filename = date_to_filename[timestamp]
        filepath = os.path.join(storage_path, filename)
        with open(filepath, 'r') as f:
            try:
                event = json.load(f)
                if not _upload_event(event, filename):
                    return False
            except json.JSONDecodeError as e:
                # a corrupt file may cause this, lets delete it
                logging.warning(f"failed to decode {filepath} with error {e}. "
                                f"It will be removed.")
            os.remove(filepath)  # if this fails we probably need a purge anyway
    return True


def _write_queue_to_disk():
    '''flushes the in memory queue to disk, making it empty in the process'''
    for timestamp in event_queue.keys():
        if not _write_json(event_queue[timestamp], _json_filename(timestamp)):
            return False
        event_queue.pop(timestamp)
    return True


def _write_json(event, filename):
    try:
        if not os.path.exists(filename):
            with open(filename, 'w') as f:
                f.write(json.dumps(event, indent=4))
    except Exception as e:
        log.error(f"Failed to write event to disk: {e}")
        return False
    return True


def _upload_event(event, filename):

    # add serial number to filename to prevent overwriting
    cloud_filename = system_metrics.get_serial_number() + '-' + filename

    # enqueue only if it passes the big query data model
    try:
        # validate and filter diagnostic data as per big query model
        validated_data = EventDataModel(**event)
    except Exception as err:
        log.error(f'Failed to enforce biquery data model on diagnostics dict {err}')
        return

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
