import datetime
import shutil
import os
import logging

from hw_diag.utilities.backup.myst import MystBackupRestore
from hw_diag.utilities.backup.thingsix import ThingsIXBackupRestore
from hw_diag.utilities.backup.nebra import NebraBackupRestore


PLUGINS = [
    MystBackupRestore,
    ThingsIXBackupRestore,
    NebraBackupRestore
]


def perform_backup(plugins=PLUGINS):
    logging.info("Starting Backup")
    # Make temp dir for backup artifacts
    utc_now = datetime.datetime.utcnow()
    tmpdir = '/tmp/%s' % utc_now.strftime('%Y%m%d%H%M%S')
    target = '/tmp/backup'
    os.mkdir(tmpdir)
    logging.info("Backup working directory: %s" % tmpdir)

    # Invoke backup "plugins"
    for plugin in plugins:
        logging.info("Running backup plugin %s" % plugin)
        current_plugin = plugin(tmpdir)
        current_plugin.backup()

    # Make tar file with the artifacts
    logging.info("Creating backup archive")
    shutil.make_archive(target, 'tar', tmpdir)

    # Cleanup
    logging.info("Post backup cleanup")
    shutil.rmtree(tmpdir)
    shutil.move('%s.tar' % target, '%s.nbf' % target)

    return '%s.nbf' % target


def perform_restore(plugins=PLUGINS):
    logging.info("Starting Restore")

    utc_now = datetime.datetime.utcnow()
    tmpdir = '/tmp/%s' % utc_now.strftime('%Y%m%d%H%M%S')

    try:
        os.mkdir(tmpdir)
    except Exception:
        shutil.rmtree(tmpdir)
        os.mkdir(tmpdir)

    target = '/tmp/restore.tar'
    shutil.unpack_archive(target, tmpdir, 'tar')

    for plugin in plugins:
        logging.info("Running restore plugin %s" % plugin)
        current_plugin = plugin(tmpdir)
        current_plugin.restore()

    shutil.rmtree(tmpdir)
    return True
