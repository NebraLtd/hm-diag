import json


TTN_CONF_FILE = '/var/nebra/ttn_conf.json'
TTN_CLUSTER_MAP = {
    'eu': 'eu1.cloud.thethings.network',
    'us': 'nam1.cloud.thethings.network',
    'au': 'au1.cloud.thethings.network'
}


def read_ttn_config():
    try:
        with open(TTN_CONF_FILE) as file_:
            ttn_config = json.loads(file_.read())

        cluster_url = ttn_config.get('ttn_cluster')
        ttn_cluster = 'eu'

        for region, url in TTN_CLUSTER_MAP:
            if url == cluster_url:
                ttn_cluster = region

        ttn_config['ttn_cluster'] = ttn_cluster

        return ttn_config
    except FileNotFoundError:
        # Config file doesn't exist yet, assume TTN not enabled.
        return {
            'ttn_enabled': False,
            'ttn_cluster': 'eu'
        }


def write_ttn_config(ttn_enabled=False, ttn_cluster='eu'):
    ttn_cluster = TTN_CLUSTER_MAP[ttn_cluster]

    ttn_config = {
        'ttn_enabled': ttn_enabled,
        'ttn_cluster': ttn_cluster
    }

    with open(TTN_CONF_FILE, "w") as file_:
        file_.write(json.dumps(ttn_config))
