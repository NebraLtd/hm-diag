from hm_pyhelper.constants.nebra import NEBRA_WALLET_ADDRESS
from hm_pyhelper.gateway_grpc.client import GatewayClient, decode_pub_key
from hm_pyhelper.miner_param import LOGGER
import grpc


def fetch_miner_data(diagnostics):
    with GatewayClient() as client:
        try:
            validator_info = client.get_validator_info()
            diagnostics['validator_address'] = decode_pub_key(validator_info.gateway.address)
            diagnostics['validator_uri'] = validator_info.gateway.uri
            diagnostics['block_age'] = validator_info.block_age
            diagnostics['MH'] = validator_info.height
            diagnostics['RE'] = client.get_region()
            diagnostics['miner_key'] = client.get_pubkey()
            diagnostics['FW'] = client.get_gateway_version()
        except grpc.RpcError as err:
            LOGGER.error(f"rpc error: {err.StatusCode}")
            LOGGER.exception(err)
        except Exception as err:
            LOGGER.exception(err)
        finally:
            return diagnostics


def create_add_gateway_txn(destination_wallet: str) -> dict:
    with GatewayClient() as client:
        add_gateway_txn = client.create_add_gateway_txn(destination_wallet,
                                                        NEBRA_WALLET_ADDRESS)
        return add_gateway_txn
