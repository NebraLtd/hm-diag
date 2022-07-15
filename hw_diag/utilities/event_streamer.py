from datetime import datetime
from enum import Enum, auto
import json
import os
import requests
import logging

log = logging.getLogger()
log.setLevel(logging.DEBUG)

VOLUME_PATH = '/var/watchdog/'

NETWORK_EVENT_BASE = 0
CONTAINER_EVENT_BASE = 1000

NETWORK_ACTION_BASE = 10000
CONTAINER_ACTION_BASE = 11000

BUCKET_NAME = os.getenv(
    'MINER_EVENTS_GCS_BUCKET',
    'helium-miner-events'
)

URL = 'https://www.googleapis.com/upload/storage/v1/b/%s/o?uploadType=media' \
    % BUCKET_NAME


event_queue = {}
EVENT_TYPE_KEY = 'event_type'
ACTION_TYPE_KEY = 'action_type'


class DiagEvent(Enum):
    NETWORK_DISCONNECTED = NETWORK_ACTION_BASE  # completely disconnected.
    NETWORK_LOCAL_CONNECTED = auto()  # connected to local gateway
    NETWORK_INTERNET_CONNECTED = auto()  # connected to internet


class DiagAction(Enum):
    ACTION_NONE = -1
    ACTION_NM_RESTART = NETWORK_ACTION_BASE
    ACTION_SYSTEM_REBOOT = auto()
    ACTION_SYSTEM_REBOOT_FORCED = auto()


def event_fingerprint(event_type, action_type=DiagAction.ACTION_NONE, msg=""):
    # right now event fingerprint is decided base on only these three"
    return f"{event_type}_{action_type}_{msg}"


def enqueue_event(event):
    event['generated_ts'] = datetime.utcnow().timestamp()
    event_queue[datetime.now()] = event

    # if we are restarting system, write events to disk, otherwise continue to process
    if event[ACTION_TYPE_KEY] in [DiagAction.ACTION_SYSTEM_REBOOT,
                                  DiagAction.ACTION_SYSTEM_REBOOT_FORCED]:
        _write_queue_to_disk()
    # not processing events here, callers shouldn't worry about errors in processing


def process_queued_events():
    # not doing any handling for error,
    # not sure much can be done.
    _process_disk_queue()
    _process_mem_queue()


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

    # create a map { timestamp: eventfile } so that we can sort and upload
    # based on timestamp
    dates_filenames = {}
    for file in os.listdir(storage_path):
        if file.endswith('.json'):
            dates_filenames[(datetime.fromisoformat(file.split('.')[0]))] = file

    # upload by timestamp
    for timestamp in sorted(dates_filenames.keys()):
        filename = dates_filenames[timestamp]
        filepath = os.path.join(storage_path, filename)
        with open(filepath, 'r') as f:
            event = json.loads(f)
            if not _upload_event(event, filename):
                return False
            os.remove(filepath, file)  # if this fails we probably need a purge anyway
    return True


def _write_queue_to_disk():
    for timestamp in event_queue.keys():
        if not _write_json(event_queue[timestamp], _json_filename(timestamp)):
            return False
    return True


def _write_json(event, filename):
    try:
        with open(filename, 'w') as f:
            f.write(json.dumps(event))
    except Exception as e:
        log.error(f"Failed to write event to disk: {e}")
        return False
    return True


def _upload_event(event, cloud_filename):
    upload_url = '%s&name=%s' % (URL, cloud_filename)
    headers = {'Content-Type': 'application/json'}

    # convert enum to string for better readability and json serialization
    event[EVENT_TYPE_KEY] = event[EVENT_TYPE_KEY].name
    event[ACTION_TYPE_KEY] = event[ACTION_TYPE_KEY].name
    content = json.dumps(event, indent=4)

    # print(f"uploading event: {content}")

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


if __name__ == '__main__':
    event = {}
    event['event_type'] = DiagEvent.NETWORK_DISCONNECTED
    event['event_type'] = event['event_type'].name
    print(json.dumps(event))
