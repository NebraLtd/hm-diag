import unittest

from hw_diag.utilities.fifo_disk_queue import FifoDiskQueue
from hw_diag.utilities.osutils import get_rw_storage_path, rm_tree_if_exists


def test_event1():
    return {
        "key1": "value1",
        "key2": []
    }


def test_event2():
    return {
        "key1": "value2",
        "key2": ["value3", "value4"]
    }


class TestFifoDiskQueue(unittest.TestCase):

    def test_peek(self):
        storage_path = get_rw_storage_path('/var/cache', 'test_fifo_disk_queue')
        rm_tree_if_exists(storage_path)
        fifo = FifoDiskQueue(storage_path, maxsize=10)
        fifo.put(test_event1())
        fifo.put(test_event2())
        # bunch of peek calls should give us the same item
        for _ in range(5):
            self.assertEqual(test_event1(), fifo.peek())
        self.assertEqual(fifo.qsize(), 2)
        # check they can be popped in the same order
        self.assertEqual(test_event1(), fifo.get())
        self.assertEqual(test_event2(), fifo.get())
        self.assertEqual(fifo.qsize(), 0)
        rm_tree_if_exists(storage_path)
