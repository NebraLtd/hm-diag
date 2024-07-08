import datetime
import shutil
import os
import logging

from hw_diag.utilities.backup.myst import MystBackupRestore
from hw_diag.utilities.backup.thingsix import ThingsIXBackupRestore
from hw_diag.utilities.backup.nebra import NebraBackupRestore
from hw_diag.utilities.backup.wingbits import WingbitsBackupRestore
from hw_diag.utilities.db import get_value, set_value
from hw_diag.utilities.crypto import empty_hash


PLUGINS = [
    MystBackupRestore,
    ThingsIXBackupRestore,
    NebraBackupRestore,
    WingbitsBackupRestore
]


def perform_backup(plugins=PLUGINS):
    logging.info("Starting Backup")
    # Make temp dir for backup artifacts
    utc_now = datetime.datetime.utcnow()
    tmpdir = '/tmp/%s' % utc_now.strftime('%Y%m%d%H%M%S')  # nosec
    target = '/tmp/backup'  # nosec
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
    tmpdir = '/tmp/%s' % utc_now.strftime('%Y%m%d%H%M%S')  # nosec

    try:
        os.mkdir(tmpdir)
    except Exception:
        shutil.rmtree(tmpdir)
        os.mkdir(tmpdir)

    target = '/tmp/restore.tar'  # nosec
    shutil.unpack_archive(target, tmpdir, 'tar')

    for plugin in plugins:
        logging.info("Running restore plugin %s" % plugin)
        current_plugin = plugin(tmpdir)
        current_plugin.restore()

    shutil.rmtree(tmpdir)
    return True


def _form_hash_storage_key(service_name: str) -> str:
    '''
    returns the key used to store sha256 hash of the service in db
    '''
    return f"{service_name}_hash"


def update_backup_checkpoint():
    '''
    updates the latest sha256 hash of identity data in db
    '''
    try:
        id_hashes = identity_hashes()
        for service_name, hash_value in id_hashes.items():
            # no need to set hash of empty values
            if hash_value != empty_hash():
                set_value(_form_hash_storage_key(service_name), id_hashes[service_name])
    except Exception as e:
        logging.error(f"couldn't store id checkpoints: {e}")


def services_pending_backup() -> list[str]:
    '''
    Returns a list of services that have pending backups
    '''
    id_hashes = identity_hashes()
    pending_for = []
    for service_name in id_hashes:
        stored_hash = get_value(_form_hash_storage_key(service_name), empty_hash())
        actual_hash = id_hashes[service_name]
        logging.debug(f"{service_name} stored hash : {stored_hash} actual: {actual_hash}")
        # if the new hash is not equal to stored or empty hash
        # a backup is warranted
        if actual_hash not in [stored_hash, empty_hash()]:
            logging.info(f"backup pending for service: {service_name}")
            pending_for.append(service_name)
    return pending_for


def identity_hashes(plugins=PLUGINS) -> dict[str, str]:
    '''
    calls all the plugins and returns a dict of service name
    and sha256 hash for their identity data.
    '''
    utc_now = datetime.datetime.utcnow()
    tmpdir = '/tmp/%s' % utc_now.strftime('%Y%m%d%H%M%S')  # nosec

    try:
        os.mkdir(tmpdir)
    except Exception:
        shutil.rmtree(tmpdir)
        os.mkdir(tmpdir)

    id_hashes = {}
    for plugin in plugins:
        current_plugin = plugin(tmpdir)
        id_hashes.update(current_plugin.identity_hash())

    shutil.rmtree(tmpdir)
    return id_hashes
