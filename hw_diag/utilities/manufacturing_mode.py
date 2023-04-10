import os
from pathlib import Path

from hw_diag.constants import MANUFACTURING_MODE_FILE_LOCATION, MANUFACTURING_MODE_ENV_VAR
from .network import manufacturing_mode_ping_check


def manufacturing_mode_file_check(
    file_path: Path = MANUFACTURING_MODE_FILE_LOCATION,
) -> bool:
    "manufacturing mode based on /var/nebra/in_manufacturing file existence is a one-shot thing"
    path_exists = False

    if file_path.exists():
        path_exists = True
        # remove the file as we want this to happen only once.
        os.remove(file_path)

    return path_exists


def manufacturing_mode_env_check(
    env_var_name: str = MANUFACTURING_MODE_ENV_VAR,
) -> bool | None:
    if env_var_name not in os.environ:
        return None

    if os.environ[env_var_name].lower() in ["true", "1", "t", "y", "yes"]:
        return True

    return False


def device_in_manufacturing():
    if manufacturing_mode_file_check() is True:
        return True

    manufacturing_mode_from_env = manufacturing_mode_env_check()
    if manufacturing_mode_from_env is not None:
        return manufacturing_mode_from_env

    return manufacturing_mode_ping_check()
