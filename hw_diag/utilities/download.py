import os.path
import requests
import shutil
import hashlib

from hm_pyhelper.logger import get_logger

logging = get_logger(__name__)


class ContentLengthError(Exception):
    pass


class MD5HashValidationError(Exception):
    pass


def validate_file(file_path: str, hash: str) -> bool:
    """
    Validates a file against an MD5 hash value

    :param file_path: path to the file for hash validation
    :param hash:      expected hash value of the file
    """
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(1000 * 1000)  # approx 1mb
            if not chunk:
                break
            md5.update(chunk)
    return md5.hexdigest() == hash


def download_with_resume(url: str, file_path: str, hash: str = '', timeout: int = 10) -> None:
    """
    Performs a HTTP(S) download that can be restarted if prematurely terminated.
    The HTTP server must support byte ranges.

    :param file_path: the path to the file to write to disk
    :param hash: hash value for file validation
    """
    # don't download if the file exists
    if os.path.exists(file_path):
        return
    block_size = 1000 * 1000  # approx 1mb
    tmp_file_path = file_path + '.part'
    first_byte = os.path.getsize(tmp_file_path) if os.path.exists(tmp_file_path) else 0
    file_mode = 'ab' if first_byte else 'wb'
    logging.debug('Starting download at %.1fMB' % (first_byte / 1e6))
    file_size = -1
    try:
        file_size = int(requests.head(url).headers['Content-length'])
        logging.info('File size is %s' % file_size)
        headers = {"Range": "bytes=%s-" % first_byte}
        req = requests.get(url, headers=headers, stream=True, timeout=timeout)
        with open(tmp_file_path, file_mode) as f:
            for chunk in req.iter_content(chunk_size=block_size):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
    except IOError as e:
        logging.error('IO Error - %s' % e)
    finally:
        # rename the temp download file to the correct name if fully downloaded
        if file_size == os.path.getsize(tmp_file_path):
            # if there's a hash value, validate the file, delete the file if hash
            # fails and raise an exception
            if hash and not validate_file(tmp_file_path, hash):
                os.remove(tmp_file_path)
                raise MD5HashValidationError('Error validating the file against its MD5 hash')
            shutil.move(tmp_file_path, file_path)
        elif file_size == -1:
            raise ContentLengthError('Error getting Content-Length from server: %s' % url)
