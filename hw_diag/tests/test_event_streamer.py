import unittest
from unittest.mock import patch
import responses
from datetime import datetime

from hw_diag.utilities.event_streamer import EVENT_TYPE_KEY, ACTION_TYPE_KEY, DiagAction, \
    DiagEvent, event_streamer, GCS_BUCKET_NAME


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
        url=f"https://www.googleapis.com/upload/storage/v1/b/{GCS_BUCKET_NAME}/o",
        status=200,
        content_type="application/json",
        body='{"success": true}',
    )


def add_upload_failure_response():
    responses.add(
        responses.POST,
        url=f"https://www.googleapis.com/upload/storage/v1/b/{GCS_BUCKET_NAME}/o",
        status=400,
        content_type="application/json",
        body='{"success": false}',
    )


class TestEventStreamer(unittest.TestCase):
    @responses.activate
    def test_enqueue_with_upload_request_failing(self):
        event_streamer.clear_queued_events()
        # make sure next two calls to upload will fail and queue builds up
        add_upload_failure_response()
        add_upload_failure_response()
        event_streamer.enqueue_persistent_event(valid_test_event())
        event_streamer.enqueue_persistent_event(valid_test_event())
        self.assertEqual(event_streamer._event_queue.qsize(), 2)

    @responses.activate
    def test_enqueue_with_upload_request_fail_success(self):
        event_streamer.clear_queued_events()
        # make sure next three calls to upload will fail
        # that means our queue should build up
        add_upload_failure_response()
        event_streamer.enqueue_persistent_event(valid_test_event())
        self.assertEqual(event_streamer._event_queue.qsize(), 1)
        # allow calls to response succeed
        add_upload_success_response()
        add_upload_success_response()
        event_streamer.enqueue_persistent_event(valid_test_event())
        self.assertEqual(event_streamer._event_queue.qsize(), 0)

    def test_enqueue_invalid_event(self):
        event_streamer.clear_queued_events()
        # make sure next two calls to upload will fail and queue builds up
        event_streamer.enqueue_persistent_event({})
        event_streamer.enqueue_persistent_event({})
        self.assertEqual(event_streamer._event_queue.qsize(), 0)

    @patch('hw_diag.utilities.event_streamer.EventStreamer.process_queued_events',
           side_effect=OSError('test exception'))
    @patch('hw_diag.utilities.event_streamer.EventStreamer.reset_queue')
    def test_process_event_failure(self, mock_reset_queue, mock_process_queued_events):
        event_streamer.clear_queued_events()
        event_streamer.enqueue_persistent_event(valid_test_event())
        self.assertEqual(mock_reset_queue.call_count, 1)
