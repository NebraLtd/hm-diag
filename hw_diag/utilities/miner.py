from hm_pyhelper.constants.nebra import NEBRA_WALLET_ADDRESS
from hm_pyhelper.miner_json_rpc import MinerClient


def create_add_gateway_txn(destination_wallet):
    client = MinerClient()
    add_gateway_txn = client.create_add_gateway_txn(destination_wallet, NEBRA_WALLET_ADDRESS)
    return add_gateway_txn
