import os
import shutil
import tempfile
import functools
import subprocess


def get_rw_storage_path(base_path: str, relative_path: str) -> str:
    '''returns combined path if writable otherwise a temporary path'''
    if os.access(base_path, os.W_OK):
        return os.path.join(base_path, relative_path)
    else:
        temp_dir = tempfile.TemporaryDirectory()
        return os.path.join(temp_dir.name, relative_path)


def rm_tree_if_exists(path: str) -> None:
    if os.path.exists(path):
        shutil.rmtree(path)


def balena_boot_partition() -> str | None:
    return find_part_with_label("resin-boot")


@functools.cache
def find_part_with_label(label) -> str | None:
    blk_info_list = balena_blk_info()

    for blk_info in blk_info_list:
        if label in blk_info.get('meta'):
            return blk_info.get('device')
    return None


@functools.cache
def balena_blk_info():
    blk_list = []
    output = subprocess.check_output('blkid').decode('utf-8')

    # each line in the output will have this form
    # /dev/sdb3: UUID="8e4a557e-ba23-4534-aee5-824927ea5b77" BLOCK_SIZE="4096"
    # TYPE="ext4" PARTUUID="944520f9-5ba6-49ee-a069-3df1aa4fbec3"
    print(output)
    for line in output.splitlines():
        print(line)
        dev_parts = line.split(':')
        if len(dev_parts) >= 2:
            blk_info = {}
            blk_info['device'] = dev_parts[0].strip()
            blk_info['meta'] = dev_parts[1].strip()
            blk_list.append(blk_info)
    return blk_list
