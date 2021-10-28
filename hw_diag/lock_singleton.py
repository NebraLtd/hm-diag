import functools
import os
import posix_ipc

LOCK_ECC = 'LOCK_ECC'


class LockSingleton(object):
    _prefix = "LockSingleton."
    _mode = 0o666

    def __init__(self, name, initial_value=1):
        self._name = self._prefix + name
        # so it doesn't interfere with our semaphore mode
        old_umask = os.umask(0)
        try:
            self._sem = posix_ipc.Semaphore(self._name,
                                            mode=self._mode,
                                            flags=posix_ipc.O_CREAT,
                                            initial_value=initial_value)
        finally:
            os.umask(old_umask)

    def acquire(self, timeout=None):
        """Acquire the lock
        """
        try:
            self._sem.acquire(timeout)
        except posix_ipc.BusyError:
            return False

        return True

    def release(self):
        """Release the lock
        """
        self._sem.release()

    def locked(self):
        return self.value() == 0

    def value(self):
        return self._sem.value


def ecc_lock(func):
    """Returns an ECC LOCK decorator.
    """
    lock = LockSingleton(LOCK_ECC)

    @functools.wraps(func)
    def wrapper_ecc_lock(*args, **kwargs):
        lock.acquire()
        value = func(*args, **kwargs)
        lock.release()
        return value
    return wrapper_ecc_lock
