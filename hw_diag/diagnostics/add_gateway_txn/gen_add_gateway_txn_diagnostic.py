import random

from hm_pyhelper.miner_json_rpc import MinerClient
from hm_pyhelper.constants.shipping import DESTINATION_ADD_GATEWAY_TXN_KEY
from hm_pyhelper.constants.nebra import NEBRA_WALLET_ADDRESS
from .base_add_gateway_txn_diagnostic import BaseAddGatewayTxnDiagnostic


class GenAddGatewayTxnDiagnostic(BaseAddGatewayTxnDiagnostic):
    """
    Generates an add_gateway_txn if a destination name and wallets are defined and valid.
    Diagnostics report will be in the format below if successful.

    https://docs.helium.com/mine-hnt/full-hotspots/become-a-maker/hotspot-integration-testing/#generate-an-add-hotspot-transaction
    {
        errors: [],
        DESTINATION_ADD_GATEWAY_TXN_KEY: {
            "address": "11TL62V8NYvSTXmV5CZCjaucskvNR1Fdar1Pg4Hzmzk5tk2JBac",
            "fee": 65000,
            "owner": "14GWyFj9FjLHzoN3aX7Tq7PL6fEg4dfWPY8CrK8b9S5ZrcKDz6S",
            "payer": "138LbePH4r7hWPuTnK6HXVJ8ATM2QU71iVHzLTup1UbnPDvbxmr",
            "staking fee": 4000000,
            "txn": "CrkBCiEBrlImpYLbJ0z0hw5b4g9isRyPrgbXs9X+RrJ4pJJc9MkS..."
        }
    }
    """

    def __init__(self):
        super(GenAddGatewayTxnDiagnostic, self). \
            __init__(DESTINATION_ADD_GATEWAY_TXN_KEY, DESTINATION_ADD_GATEWAY_TXN_KEY)

    def select_and_validate_one_destination_wallet(self):
        """
        Randomly pick a destination wallet and ensure it is not empty.
        """
        self.destination_wallet = random.choice(self.destination_wallets)
        is_destination_wallet_valid = self.destination_wallet is not None and \
            len(self.destination_wallet) > 1

        if not is_destination_wallet_valid:
            msg = f'Wallet selected as owner is invalid ({self.destination_wallet})'
            self.diagnostics_report.record_failure(msg, self)
            return False
        else:
            return True

    def gen_add_gateway_txn(self):
        """
        Gen add_gateway_txn over RPC. This may raise an exception, which should be handled
        by the caller.
        """
        # Send json RPC request to create gateway transaction
        miner_rpc = MinerClient()
        add_gateway_txn = miner_rpc.create_add_gateway_txn(self.destination_wallet,
                                                           NEBRA_WALLET_ADDRESS)
        self.diagnostics_report.record_result(add_gateway_txn, self)
        return True

    def get_steps(self):
        return [
            self.load_and_validate_nebra_json,
            self.load_and_validate_destination_wallets,
            self.select_and_validate_one_destination_wallet,
            self.gen_add_gateway_txn
        ]
