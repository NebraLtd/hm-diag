import requests
import os

HELIUM_MINER_HEIGHT_URL = os.getenv(
    'HELIUM_MINER_HEIGHT_URL',
    'https://api.helium.io/v1/blocks/height'
)


def get_helium_blockchain_height():
    """
    Get the blockchain height from the Helium API

    output: return current blockchain height from the Helium API
    Possible exceptions:
    TypeError - if the key ['data']['height'] in response is not found.
    """
    headers = {
                'user-agent': 'Mozilla/5.0 (X11; U; Linux i686; it; rv:1.9.0.10)'%
                ' Gecko/2009042513 Ubuntu/8.04 (hardy) Firefox/3.0.10',
              }
    result = requests.get(HELIUM_MINER_HEIGHT_URL,
                          headers=headers,
                          timeout=os.getenv('HELIUM_API_TIMEOUT_SECONDS', 5))
    if result.status_code == 200:
        result = result.json()
        try:
            result = result['data']['height']
        except KeyError:
            raise KeyError(
                "Not found value from key ['data']['height'] in json"
            )
        return result
    else:
        print("Request failed %s" % result)
        return None
