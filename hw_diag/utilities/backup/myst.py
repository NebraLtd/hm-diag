import os
import shutil

from hw_diag.utilities.backup.base import BaseBackupRestore


MYST_DIR = '/var/myst'


class MystBackupRestore(BaseBackupRestore):
    name = 'MYST'

    def backup(self):
        shutil.copytree(MYST_DIR, self.tmpdir)

    def restore(self):
        os.system('cp -r %s/* %s/.' % (self.tmpdir, MYST_DIR))
