from hm_pyhelper.constants.nebra import NEBRA_WALLET_ADDRESS
from hm_pyhelper.miner_json_rpc import MinerClient
from hm_pyhelper.miner_json_rpc.exceptions import MinerFailedFetchData
from hm_pyhelper.miner_param import LOGGER


def fetch_miner_data(diagnostics):
    client = MinerClient()
    try:
        peerbook = client.get_peer_book()[0]
        height = client.get_height()
    except MinerFailedFetchData as err:
        LOGGER.exception(err)
        diagnostics['MC'] = "Failed to Fetch"
        diagnostics['MD'] = "Failed to Fetch"
        diagnostics['MH'] = None
        diagnostics['MN'] = "Failed to Fetch"
        diagnostics['MR'] = "Failed to Fetch"
        return diagnostics
    except Exception as err:
        LOGGER.exception(err)
        diagnostics['MC'] = "Failed to Fetch"
        diagnostics['MD'] = "Failed to Fetch"
        diagnostics['MH'] = None
        diagnostics['MN'] = "Failed to Fetch"
        diagnostics['MR'] = "Failed to Fetch"
        return diagnostics

    diagnostics['MC'] = peerbook.get('connection_count') > 1
    diagnostics['MD'] = peerbook.get('listen_addr_count') > 0
    diagnostics['MH'] = height.get('height')
    diagnostics['MN'] = peerbook.get('nat')
    diagnostics['MR'] = diagnostics['MN'] == 'symmetric'
    return diagnostics


def create_add_gateway_txn(destination_wallet):
    client = MinerClient()
    add_gateway_txn = client.create_add_gateway_txn(destination_wallet, NEBRA_WALLET_ADDRESS)
    return add_gateway_txn
