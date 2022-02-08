import json
from typing import Any


class KeyStore:
    ''' A simple sync key value store that stores valuse in a json file'''

    def __init__(self, filename: str) -> None:
        '''
        :param filename: The filename to store the data in
        '''
        self.filename = filename
        self.store = {}
        try:
            with open(self.filename, 'r') as f:
                self.store = json.load(f)
        except FileNotFoundError:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        '''
        :param key: The key to get the value for
        :param default: The default value to return if the key is not found
        '''
        return self.store.get(key, default)

    def set(self, key: str, value: Any) -> None:
        '''
        :param key: The key to set the value for
        :param value: The value to set
        '''
        self.store[key] = value
        with open(self.filename, 'w') as f:
            f.write(json.dumps(self.store, indent=4))


if __name__ == "__main__":
    ks = KeyStore("keystore.json")
    ks.set("foo", "bar")

    ks1 = KeyStore("keystore.json")
    print(ks1.get("foo"))
