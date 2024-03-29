import os
import shutil

from hw_diag.utilities.backup.base import BaseBackupRestore


DB_FILE = '/var/data/hm_diag.db'


class NebraBackupRestore(BaseBackupRestore):
    name = 'NEBRA'

    def backup(self):
        os.mkdir(self.tmpdir)
        shutil.copyfile(DB_FILE, '%s/hm_diag.db' % self.tmpdir)

    def restore(self):
        os.system('cp %s/hm_diag.db %s' % (self.tmpdir, DB_FILE))  # nosec
