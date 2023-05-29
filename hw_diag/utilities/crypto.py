import hashlib

from hm_pyhelper.logger import get_logger

logging = get_logger(__name__)


def calculate_file_hash(files: list[str],
                        hash_algorithm='sha256',
                        block_size=4096):
    '''returns combined hash of a list of files'''
    hash_object = hashlib.new(hash_algorithm)

    for file_path in files:
        with open(file_path, 'rb') as file:
            # Read the file in chunks to handle large files efficiently
            for chunk in iter(lambda: file.read(block_size), b''):
                hash_object.update(chunk)
    logging.debug(f"hash for {files} is : {hash_object.hexdigest()}")
    return hash_object.hexdigest()


def empty_hash(hash_algorithm='sha256', block_size=4096):
    '''return hash of an empty string'''
    return calculate_file_hash([], hash_algorithm, block_size)
