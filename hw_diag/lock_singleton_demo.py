import time
from hw_diag.lock_singleton import ecc_lock


@ecc_lock
def worker1():
    print('Start working...')
    time.sleep(5)
    print('Work finished!')


worker1()
