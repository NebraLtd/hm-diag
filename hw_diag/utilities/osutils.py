import os
import shutil
import tempfile


def get_rw_storage_path(base_path: str, relative_path: str) -> str:
    '''returns combined path if writable otherwise a temporary path'''
    if os.access(base_path, os.W_OK):
        return os.path.join(base_path, relative_path)
    else:
        temp_dir = tempfile.TemporaryDirectory()
        return os.path.join(temp_dir.name, relative_path)


def rm_tree_if_exists(path: str) -> None:
    if os.path.exists(path):
        shutil.rmtree(path)
