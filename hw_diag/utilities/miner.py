from hm_pyhelper.constants.nebra import NEBRA_WALLET_ADDRESS
from hm_pyhelper.gateway_grpc.client import GatewayClient, decode_pub_key


def fetch_miner_data(diagnostics: dict) -> dict:
    with GatewayClient() as client:
        validator_info = client.get_validator_info()
        diagnostics['validator_address'] = decode_pub_key(validator_info.gateway.address)
        diagnostics['validator_uri'] = validator_info.gateway.uri
        diagnostics['block_age'] = validator_info.block_age
        diagnostics['MH'] = validator_info.height
        diagnostics['RE'] = client.get_region()
        diagnostics['miner_key'] = client.get_pubkey()
    return diagnostics


def create_add_gateway_txn(destination_wallet: str) -> dict:
    with GatewayClient() as client:
        add_gateway_txn = client.create_add_gateway_txn(destination_wallet,
                                                        NEBRA_WALLET_ADDRESS)
        return add_gateway_txn
