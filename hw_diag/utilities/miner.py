import json
import logging
import subprocess

from hm_pyhelper.miner_json_rpc import MinerClient


client = MinerClient()


def get_gateway_mfr_test_result():
    """
    Run gateway_mfr test and report back.
    """
    try:
        run_gateway_mfr_keys = subprocess.run(
            ["/usr/local/bin/gateway_mfr", "test"],
            capture_output=True,
            check=True
        )
    except subprocess.CalledProcessError:
        logging.error("gateway_mfr exited with a non-zero status")
        return False

    try:
        return json.loads(run_gateway_mfr_keys.stdout)
    except json.JSONDecodeError:
        logging.error("Unable to parse JSON from gateway_mfr")
    return False


def fetch_miner_data(diagnostics):
    # Fetch miner keys from miner container and append
    # them to the diagnostics dictionary.
    try:
        public_key = client.get_peer_addr().get('peer_addr').split('/')[2]
        peerbook = client.get_peer_book()[0]
        height = client.get_height()
    except Exception as err:
        raise Exception("Unable to fetch keys from miner container "
                        "via JSON RPC API. Exception: %s" % str(err))

    diagnostics['PK'] = public_key
    diagnostics['OK'] = public_key
    diagnostics['AN'] = peerbook.get('name')
    diagnostics['MC'] = peerbook.get('connection_count') > 1
    diagnostics['MD'] = peerbook.get('listen_addr_count') > 0
    diagnostics['MH'] = height.get('height')
    diagnostics['MN'] = peerbook.get('nat')
    diagnostics['MR'] = diagnostics['MN'] == 'symmetric'
    return diagnostics