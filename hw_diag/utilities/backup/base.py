

class BaseBackupRestore(object):
    name = 'BASE'
    tmpdir = None

    def __init__(self, tmpdir):
        self.tmpdir = '%s/%s' % (tmpdir, self.name)

    def identity_hash(self) -> dict[str, str]:
        '''
        returns a dict of where key is a friendly name of service
        and value is sha256 hash of identity data.
        We use it to decide if a backup is needed or not.
        if there is no identity data, return empty dict
        '''
        return {}

    def backup(self):
        pass

    def restore(self):
        pass
