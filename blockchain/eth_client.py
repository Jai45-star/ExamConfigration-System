# blockchain/eth_client.py — Ethereum Sepolia se connect karne ke liye.
from web3 import Web3
from config import get_settings
from blockchain.contract_interface import ENTRY_LEDGER_ABI
from utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

def _inject_poa_middleware(w3: Web3) -> None:
    # Sepolia jaise PoA networks ke liye middleware inject karna
    try:
        from web3.middleware import ExtraDataToPOAMiddleware
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    except ImportError:
        from web3.middleware import geth_poa_middleware  # type: ignore
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)

class EthClient:
    def __init__(self):
        self.w3 = None
        self.account = None
        self.contract = None

        if not settings.ETH_NODE_URL:
            logger.warning("ETH_NODE_URL nahi mila — blockchain band rahegi.")
            return

        # Ethereum node se connect karna
        self.w3 = Web3(Web3.HTTPProvider(settings.ETH_NODE_URL))
        _inject_poa_middleware(self.w3)

        if not self.w3.is_connected():
            logger.warning(f"Primary RPC ({settings.ETH_NODE_URL}) fail ho gaya. Public RPC try kar rahe hain...")
            # Fallback to a public Sepolia RPC
            public_rpc = "https://ethereum-sepolia-rpc.publicnode.com"
            self.w3 = Web3(Web3.HTTPProvider(public_rpc))
            _inject_poa_middleware(self.w3)
            
            if not self.w3.is_connected():
                raise ConnectionError(f"Ethereum network se connect nahi ho paye: Na toh Alchemy na hi Public RPC kaam kar raha hai.")
            logger.success(f"Public RPC se connection ban gaya!")

        if not settings.ADMIN_WALLET_PRIVATE_KEY:
            logger.warning("Private key nahi mili — results simulate honge.")
            return

        # Wallet setup karna
        self.account = self.w3.eth.account.from_key(settings.ADMIN_WALLET_PRIVATE_KEY)

        # Smart contract connect karna
        if settings.CONTRACT_ADDRESS:
            self.contract = self.w3.eth.contract(
                address=self.w3.to_checksum_address(settings.CONTRACT_ADDRESS),
                abi=ENTRY_LEDGER_ABI
            )
        else:
            logger.warning("Contract address nahi mila.")

    def record_entry_on_chain(self, roll_number: str, exam_id: str, token_hash: str, timestamp: int):
        # Entry ko permanent record (Blockchain) par likhna.
        if not self.w3 or not self.contract:
            logger.warning("Blockchain setup nahi hai, dummy hash bhej rahe hain.")
            return "SIMULATED_RECORD_OK", 0

        # Nonce mangwana (Transaction sequence number)
        nonce = self.w3.eth.get_transaction_count(self.account.address)

        # Transaction taiyar karna
        tx = self.contract.functions.recordEntry(
            roll_number, exam_id, token_hash, timestamp
        ).build_transaction({
            "chainId": settings.CHAIN_ID,
            "gas": 250_000,
            "gasPrice": self.w3.eth.gas_price,
            "nonce": nonce,
        })

        # Transaction sign karke bhej dena
        signed_tx = self.w3.eth.account.sign_transaction(tx, private_key=self.account.key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        # Confirmation ka wait karna
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        if receipt.status != 1:
            raise RuntimeError(f"Blockchain entry fail ho gayi hash: {tx_hash.hex()}")

        return tx_hash.hex(), receipt.blockNumber

    def verify_entry_on_chain(self, token_hash: str):
        # Check karna ki entry blockchain par hai ya nahi.
        if not self.w3 or not self.contract:
            return None
        return self.contract.functions.verifyEntry(token_hash).call()

# Ek single instance banana poori app ke liye
eth_client = None
try:
    eth_client = EthClient()
except Exception as exc:
    logger.error(f"Blockchain setup nahi chal paya: {exc}")
