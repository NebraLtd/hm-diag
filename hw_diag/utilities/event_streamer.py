from enum import Enum, auto
import os
import json
import shutil
import requests
import logging
import threading

from persistqueue.exceptions import Full
from json import JSONDecodeError
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
MISC_EVENT_BASE = 2000

NETWORK_ACTION_BASE = 10000
CONTAINER_ACTION_BASE = 11000

EVENT_TYPE_KEY = 'event_type'
ACTION_TYPE_KEY = 'action_type'

GCS_BUCKET_NAME = os.getenv(
    'MINER_EVENTS_GCS_BUCKET',
    'helium-miner-events'
)

URL = 'https://www.googleapis.com/upload/storage/v1/b/%s/o?uploadType=media' \
    % GCS_BUCKET_NAME


class DiagEvent(Enum):
    NETWORK_DISCONNECTED = NETWORK_ACTION_BASE  # completely disconnected.
    NETWORK_LOCAL_CONNECTED = auto()  # connected to local gateway
    NETWORK_INTERNET_CONNECTED = auto()  # connected to internet
    HEARTBEAT = MISC_EVENT_BASE


class DiagAction(Enum):
    ACTION_NONE = -1
    ACTION_NM_RESTART = NETWORK_ACTION_BASE
    ACTION_SYSTEM_REBOOT = auto()
    ACTION_SYSTEM_REBOOT_FORCED = auto()


def _upload_event(event: dict) -> bool:
    '''returns false if network request fails'''

    # add serial number to filename to prevent overwriting
    cloud_filename = f'{system_metrics.get_serial_number()}-{event["generated_ts"]}.json'

    upload_url = '%s&name=%s' % (URL, cloud_filename)
    headers = {'Content-Type': 'application/json'}
    content = json.dumps(event)

    log.debug(f"uploading event: {content}")

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


def event_fingerprint(event_type: DiagEvent,
                      action_type: DiagEvent = DiagAction.ACTION_NONE,
                      msg: str = "") -> str:
    # right now event fingerprint is decided base on only these three"
    fingerprint = f"{event_type}_{action_type}_{msg}"
    return fingerprint[:128]


class EventStreamer(object):
    def __init__(self, max_size=1000) -> None:
        self.processing_lock = threading.Lock()
        self._max_size = max_size
        self._storage_path = get_rw_storage_path(VOLUME_PATH, EVENTS_FOLDER)
        self._event_queue = FifoDiskQueue(self._storage_path, maxsize=self._max_size)

    def reset_queue(self) -> None:
        self._event_queue.close()
        shutil.rmtree(self._storage_path)
        self._event_queue = FifoDiskQueue(self._storage_path, maxsize=self._max_size)

    def clear_queued_events(self) -> None:
        while not self._event_queue.empty():
            self._event_queue.get()
            self._event_queue.task_done()

    def is_event_valid(self, event: dict) -> bool:
        try:
            EventDataModel(**event)
        except Exception as e:
            logging.error(
                f"failed to enforce bigquery datamodel, modify schema or event to fix: {e}")
            return False
        return True

    def _enqueue_event_after_validation(self, event: dict) -> None:
        if not self.is_event_valid(event):
            return

        try:
            self._event_queue.put(event)
        except Full as e:
            logging.error(f"event queue is full, dropping event: {e}")
        except Exception as e:
            logging.error(f"failed to enqueue event: {e}")

    def enqueue_event(self, event: dict) -> None:
        if not self.is_event_valid(event):
            return
        _upload_event(event)

    def enqueue_persistent_event(self, event: dict) -> None:
        self._enqueue_event_after_validation(event)
        # if process events throws exception, empty the queue to recover
        try:
            self.process_queued_events()
        except (OSError, JSONDecodeError) as e:
            logging.error(f"emptying queue due to corruption: {e}")
            self.reset_queue()

    def process_queued_events(self) -> None:
        # even though event queue is thread safe
        # we are doing multiple operations potentially from different threads
        with self.processing_lock:
            while not self._event_queue.empty():
                # we don't need to worry about get blocking as we are not working with
                # threads here.
                event = self._event_queue.peek()
                if not _upload_event(event):
                    return
                # remove the event from the queue
                self._event_queue.get()
                self._event_queue.task_done()


event_streamer = EventStreamer()
