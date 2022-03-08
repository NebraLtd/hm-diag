import time
from hw_diag.utilities.dbus_proxy.dbus_ids import DBusIds
from hw_diag.utilities.dbus_proxy.dbus_object import DBusObject


class SystemDUnit(DBusObject):
    '''
    represents a systemd unit with a few convenience methods
    '''

    def __init__(self, unit_obj_path: str) -> None:
        super(SystemDUnit, self).__init__(DBusIds.SYSTEMD_SERVICE, unit_obj_path,
                                          DBusIds.SYSTEMD_UNIT_IF)

    def start(self, mode: str = 'fail') -> str:
        job_path = self._object_if.Start(mode)
        return job_path

    def stop(self, mode: str = 'fail') -> str:
        job_path = self._object_if.Stop(mode)
        return job_path

    def restart(self, mode: str = 'fail') -> str:
        job_path = self._object_if.Restart(mode)
        return job_path

    def _wait_state(self, target_state: str, timeout: int) -> bool:
        sleep_time = 1  # seconds
        max_polls = int(timeout / sleep_time)
        for _ in range(max_polls):
            time.sleep(sleep_time)
            if self.get_property('SubState').strip() == target_state:
                return True
        return False

    def wait_stop(self, mode: str = 'fail', timeout=10) -> bool:
        '''
        issues stop command and wait for max timeout secs for it to stop
        @param mode: dbus unit start/stop modes. Default is good for most cases
        @param timeout: max time to wait for stop in secs
        @rtype: true if stopped else false
        '''
        self.stop()
        return self._wait_state('dead', timeout)

    def wait_start(self, mode: str = 'fail', timeout=10) -> bool:
        '''
        issues start command and wait for max timeout secs for it to stop
        @param mode: dbus unit start/stop modes. Default is good for most cases
        @param timeout: max time to wait for stop in secs
        @rtype: true if started else false
        '''
        self.start(mode)
        return self._wait_state('running', timeout)

    def wait_restart(self, mode: str = 'fail', timeout=20) -> bool:
        '''
        issues restart command and wait for max timeout secs for it to stop
        @param mode: dbus unit start/stop modes. Default is good for most cases
        @param timeout: max time to wait for stop in secs
        @rtype: true if restarted else false
        '''
        self.restart(mode)
        # wait for the command to have an effect
        time.sleep(2)
        return self._wait_state('running', timeout)

    def is_running(self) -> bool:
        return self.get_property('SubState').strip() == 'running'

    def is_stopped(self) -> bool:
        return self.get_property('SubState').strip() == 'dead'
