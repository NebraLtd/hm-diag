"Test cases for manufacturing mode determination check"
import os
import subprocess
from tempfile import NamedTemporaryFile
from pathlib import Path
from unittest import mock

import pytest

from ..constants import MANUFACTURING_MODE_ENV_VAR
from ..utilities.manufacturing_mode import (
    manufacturing_mode_file_check,
    manufacturing_mode_env_check,
    manufacturing_mode_ping_check,
)

TEMP_MANUFACTURING_MODE_FILE = "/tmp/nebra_in_manufacturing"


@pytest.fixture()
def set_manufacturing_mode_env_var_to_true():
    with mock.patch.dict("os.environ"):
        os.environ[MANUFACTURING_MODE_ENV_VAR] = "true"
        yield


@pytest.fixture()
def set_manufacturing_mode_env_var_to_false():
    with mock.patch.dict("os.environ"):
        os.environ[MANUFACTURING_MODE_ENV_VAR] = "false"
        yield


@pytest.fixture()
def unset_manufacturing_mode_env():
    with mock.patch.dict("os.environ"):
        if MANUFACTURING_MODE_ENV_VAR in os.environ:
            del os.environ[MANUFACTURING_MODE_ENV_VAR]
        yield


def test_manufacturing_mode_file_check():
    fp = NamedTemporaryFile(delete=False)
    fp.close()

    filepath = Path(fp.name)
    assert manufacturing_mode_file_check(filepath) is True

    # test should have already deleted the file so second check show return False
    assert manufacturing_mode_file_check(filepath) is False


def test_manufacturing_mode_enabled_via_env(set_manufacturing_mode_env_var_to_true):
    assert manufacturing_mode_env_check() is True


def test_manufacturing_mode_disabled_via_env(set_manufacturing_mode_env_var_to_false):
    assert manufacturing_mode_env_check() is False


def test_manufacturing_mode_unset_via_env(unset_manufacturing_mode_env):
    assert manufacturing_mode_env_check() is None


def test_manufacturing_mode_disabled_via_ping_check():
    with mock.patch(
        "hw_diag.utilities.network.subprocess.check_output", return_value=1
    ) as mocked_ping:
        mocked_ping.side_effect = subprocess.CalledProcessError(
            cmd="ping", returncode=1
        )
        ret = manufacturing_mode_ping_check()
        assert mocked_ping.called is True
        assert ret is False


def test_manufacturing_mode_enabled_via_ping_check():
    cmd_response = (
            b'PING 192.168.220.1 (192.168.220.1) 56(84) bytes of data.\n'
            b'64 bytes from 192.168.220.1: icmp_seq=1 ttl=64 time=25.6 ms\n'
            b'64 bytes from 192.168.220.1: icmp_seq=2 ttl=64 time=25.7 ms\n\n'
            b'--- 192.168.220.1 ping statistics ---\n'
            b'2 packets transmitted, 2 received, 0% packet loss, time 501ms\n'
            b'rtt min/avg/max/mdev = 25.608/25.641/25.674/0.033 ms\n'
        )

    with mock.patch(
        "hw_diag.utilities.network.subprocess.check_output", return_value=cmd_response
    ) as mocked_ping:

        ret = manufacturing_mode_ping_check()
        assert mocked_ping.called is True
        assert ret is True


def test_manufacturing_mode_disabled_via_successful_ping_check():
    cmd_response = (
            b'PING 192.168.220.1 (192.168.220.1) 56(84) bytes of data.\n'
            b'64 bytes from 192.168.220.1: icmp_seq=1 ttl=247 time=25.6 ms\n'
            b'64 bytes from 192.168.220.1: icmp_seq=2 ttl=247 time=25.7 ms\n\n'
            b'--- 192.168.220.1 ping statistics ---\n'
            b'2 packets transmitted, 2 received, 0% packet loss, time 501ms\n'
            b'rtt min/avg/max/mdev = 25.608/25.641/25.674/0.033 ms\n'
        )

    with mock.patch(
        "hw_diag.utilities.network.subprocess.check_output", return_value=cmd_response
    ) as mocked_ping:

        ret = manufacturing_mode_ping_check()
        assert mocked_ping.called is True
        assert ret is False
