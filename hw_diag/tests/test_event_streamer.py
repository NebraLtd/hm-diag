import unittest
import responses
from datetime import datetime

from hw_diag.utilities.event_streamer import EVENT_TYPE_KEY, ACTION_TYPE_KEY, DiagAction, \
    DiagEvent, enqueue_event, event_queue, empty_queued_events


def valid_test_event():
    return {
        EVENT_TYPE_KEY: DiagEvent.NETWORK_DISCONNECTED.name,
        ACTION_TYPE_KEY: DiagAction.ACTION_NM_RESTART.name,
        "msg": "network is disconnected",
        "generated_ts": datetime.now().timestamp(),
        "balena_failed_containers": []
    }


def add_upload_success_response():
    responses.add(
        responses.POST,
        url="https://www.googleapis.com/upload/storage/v1/b/helium-miner-events/o",
        status=200,
        content_type="application/json",
        body='{"success": true}',
    )


def add_upload_failure_response():
    responses.add(
        responses.POST,
        url="https://www.googleapis.com/upload/storage/v1/b/helium-miner-events/o",
        status=400,
        content_type="application/json",
        body='{"success": false}',
    )


class TestEventStreamer(unittest.TestCase):
    @responses.activate
    def test_enqueue_with_upload_request_failing(self):
        empty_queued_events()
        # make sure next two calls to upload will fail and queue builds up
        add_upload_failure_response()
        add_upload_failure_response()
        enqueue_event(valid_test_event())
        enqueue_event(valid_test_event())
        self.assertEqual(event_queue.qsize(), 2)

    @responses.activate
    def test_enqueue_with_upload_request_fail_success(self):
        empty_queued_events()
        # make sure next three calls to upload will fail
        # that means our queue should build up
        add_upload_failure_response()
        enqueue_event(valid_test_event())
        self.assertEqual(event_queue.qsize(), 1)
        # allow calls to response succeed
        add_upload_success_response()
        add_upload_success_response()
        enqueue_event(valid_test_event())
        self.assertEqual(event_queue.qsize(), 0)

    def test_enqueue_invalid_event(self):
        empty_queued_events()
        # make sure next two calls to upload will fail and queue builds up
        enqueue_event({})
        enqueue_event({})
        self.assertEqual(event_queue.qsize(), 0)
