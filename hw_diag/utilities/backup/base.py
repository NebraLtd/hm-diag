

class BaseBackupRestore(object):
    name = 'BASE'
    tmpdir = None

    def __init__(self, tmpdir):
        self.tmpdir = '%s/%s' % (tmpdir, self.name)

    def backup(self):
        pass

    def restore(self):
        pass
