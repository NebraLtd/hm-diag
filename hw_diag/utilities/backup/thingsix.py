import os
import shutil
import yaml

from hw_diag.utilities.backup.base import BaseBackupRestore
from hw_diag.utilities.crypto import calculate_file_hash

from hm_pyhelper.logger import get_logger

logging = get_logger(__name__)

THIX_DIR = '/var/thix'


class ThingsIXBackupRestore(BaseBackupRestore):
    name = 'THINGSIX'

    def backup(self):
        shutil.copytree(THIX_DIR, self.tmpdir)

    def restore(self):
        os.system('cp -r %s/* %s/.' % (self.tmpdir, THIX_DIR))  # nosec
        
    def identity_hash(self) -> dict[str, str]:
        file_paths = [f"{THIX_DIR}/gateways.yaml"]

        # check if the file is valid json document
        for file in file_paths:
            try:
                with open(file, 'r') as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                logging.error(f"corrupt file: {file} : {e}")
                file_paths.remove(file)

        return {'Thingsix': calculate_file_hash(file_paths)}
