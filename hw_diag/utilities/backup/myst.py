import os
import shutil
import glob
import json

from hw_diag.utilities.backup.base import BaseBackupRestore
from hw_diag.utilities.crypto import calculate_file_hash

from hm_pyhelper.logger import get_logger

logging = get_logger(__name__)

MYST_DIR = '/var/myst'


class MystBackupRestore(BaseBackupRestore):
    name = 'MYST'

    def backup(self):
        shutil.copytree(MYST_DIR, self.tmpdir)

    def restore(self):
        os.system('cp -r %s/* %s/.' % (self.tmpdir, MYST_DIR))  # nosec

    def identity_hash(self) -> dict[str, str]:
        # find the file matching UTC* in myst key store
        file_paths = glob.glob(f'{MYST_DIR}/keystore/UTC*')
        logging.debug(f"myst keystore files: {file_paths}")
        # check if the file is valid json document
        for file in file_paths:
            try:
                with open(file, 'r') as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                logging.error(f"corrupt file: {file} : {e}")
                file_paths.remove(file)
            except Exception as e:
                logging.error(f"error reading file: {file} : {e}")
                file_paths.remove(file)

        return {'Mysterium': calculate_file_hash(file_paths)}
