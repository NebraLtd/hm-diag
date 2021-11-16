import requests


def get_helium_blockchain_height():
    """
    Get the blockchain height from the Helium API

    output: return current blockchain height from the Helium API
    Possible exceptions:
    TypeError - if the key ['data']['height'] in response is not found.
    """
    try:
        result = requests.get('https://api.helium.io/v1/blocks/height',\
                              timeout=5)
        if result.status_code == 200:
            result = result.json()
            try:
                result = result['data']['height']
            except KeyError:
                raise KeyError(
                    "Not found value from key ['data']['height'] in json"
                )
            return result
    except (requests.exceptions.ConnectTimeout,\
            requests.exceptions.ReadTimeout):
        raise
