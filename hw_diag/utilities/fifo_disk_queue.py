from persistqueue import Queue
from time import time as _time
from persistqueue.exceptions import Empty


class FifoDiskQueue(Queue):
    '''extends persistqueue.Queue class to implement peek method'''

    def __init__(self, path, maxsize=0):
        super().__init__(path, maxsize=maxsize)

    def peek(self, block=True, timeout=None):
        self.not_empty.acquire()
        try:
            if not block:
                if not self._qsize():
                    raise Empty
            elif timeout is None:
                while not self._qsize():
                    self.not_empty.wait()
            elif timeout < 0:
                raise ValueError("'timeout' must be a non-negative number")
            else:
                endtime = _time() + timeout
                while not self._qsize():
                    remaining = endtime - _time()
                    if remaining <= 0.0:
                        raise Empty
                    self.not_empty.wait(remaining)
            item = self._peek()
            return item
        finally:
            self.not_empty.release()

    def peek_nowait(self):
        return self.get(False)

    def _peek(self):
        tnum, tcnt, toffset = self.info['tail']
        hnum, hcnt, _ = self.info['head']
        if [tnum, tcnt] >= [hnum, hcnt]:
            return None
        old_pos = self.tailf.tell()
        data = self.serializer.load(self.tailf)
        self.tailf.seek(old_pos)
        return data

    def close(self):
        for fd in [self.headf, self.tailf]:
            if fd and not fd.closed:
                fd.close()
