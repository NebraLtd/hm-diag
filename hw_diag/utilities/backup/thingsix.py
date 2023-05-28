import os
import shutil

from hw_diag.utilities.backup.base import BaseBackupRestore


THIX_DIR = '/var/thix'


class ThingsIXBackupRestore(BaseBackupRestore):
    name = 'THINGSIX'

    def backup(self):
        shutil.copytree(THIX_DIR, self.tmpdir)

    def restore(self):
        os.system('cp -r %s/* %s/.' % (self.tmpdir, THIX_DIR))  # nosec
