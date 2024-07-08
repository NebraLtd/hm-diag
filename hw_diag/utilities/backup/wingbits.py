import os
import shutil

from hw_diag.utilities.backup.base import BaseBackupRestore


CONFIG_FILE = '/var/nebra/wingbits.json'


class WingbitsBackupRestore(BaseBackupRestore):
    name = 'WINGBITS'

    def backup(self):
        os.mkdir(self.tmpdir)
        shutil.copyfile(CONFIG_FILE, '%s/wingbits.json' % self.tmpdir)

    def restore(self):
        os.system('cp %s/wingbits.json %s' % (self.tmpdir, CONFIG_FILE))  # nosec
