import json
import os
import shutil

import gnupg


class GnuPG(object):
    def __init__(self, gnupghome: str = None):
        if gnupghome and not os.path.isdir(gnupghome):
            os.makedirs(gnupghome)

        self.gpg = gnupg.GPG(gnupghome=gnupghome)

    def import_keys(self, key_data: str):
        self.gpg.import_keys(key_data)

    def get_verified_json(self, data: bytes) -> object:
        """This decryption performs a signature validation and separate the payload from the rest of
        the signature and not doing any real decryption because the message is ent in cleartext."""
        decrypted_data = self.gpg.decrypt(data)

        if decrypted_data.valid:
            json_data = json.loads(str(decrypted_data))
            return json_data

        return None

    def cleanup(self) -> None:
        """Remove the homedir if was previously configured to clean the imported keys."""
        if self.gpg.gnupghome:
            shutil.rmtree(self.gpg.gnupghome)
