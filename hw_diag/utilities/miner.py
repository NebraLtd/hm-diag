from hm_pyhelper.constants.nebra import NEBRA_WALLET_ADDRESS
from hm_pyhelper.gateway_grpc.client import GatewayClient


def create_add_gateway_txn(destination_wallet: str) -> dict:
    with GatewayClient() as client:
        add_gateway_txn = client.create_add_gateway_txn(destination_wallet,
                                                        NEBRA_WALLET_ADDRESS)
        return add_gateway_txn
