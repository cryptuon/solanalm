"""
Solana Payment Client

Handles SOL micro-transactions for inference requests and training rewards.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solana.keypair import Keypair
from solana.system_program import TransferParams, transfer
from solana.transaction import Transaction
from solana.publickey import PublicKey
from solana.rpc.types import TxOpts

from core.models.schemas import PaymentRequest, PaymentResult

logger = logging.getLogger(__name__)


class SolanaPaymentClient:
    """Client for handling Solana payments"""

    def __init__(self, rpc_url: str = "https://api.devnet.solana.com"):
        self.rpc_url = rpc_url
        self.client: Optional[AsyncClient] = None
        self.treasury_keypair: Optional[Keypair] = None

        # Payment tracking
        self.pending_payments: Dict[str, PaymentRequest] = {}
        self.payment_history: Dict[str, PaymentResult] = {}

    async def initialize(self):
        """Initialize the Solana client"""
        logger.info("Initializing Solana payment client")

        # Create async RPC client
        self.client = AsyncClient(self.rpc_url)

        # TODO: Load treasury keypair from secure storage
        # For now, generate a temporary keypair for development
        self.treasury_keypair = Keypair()

        logger.info(f"Treasury wallet: {self.treasury_keypair.public_key}")

        # Check connection
        try:
            health = await self.client.is_connected()
            if health:
                logger.info("Successfully connected to Solana network")
            else:
                logger.error("Failed to connect to Solana network")
        except Exception as e:
            logger.error(f"Solana connection error: {e}")

    async def close(self):
        """Close the Solana client"""
        if self.client:
            await self.client.close()

    async def process_payment(
        self,
        from_wallet: str,
        to_wallet: str,
        amount: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentResult:
        """Process a payment between wallets"""
        if not self.client:
            raise RuntimeError("Solana client not initialized")

        try:
            # Convert SOL to lamports (1 SOL = 1e9 lamports)
            lamports = int(amount * 1_000_000_000)

            # Create public keys
            from_pubkey = PublicKey(from_wallet)
            to_pubkey = PublicKey(to_wallet)

            # For now, simulate payment processing
            # In production, this would require the user to sign the transaction
            payment_result = await self._simulate_payment(
                from_pubkey, to_pubkey, lamports, metadata or {}
            )

            return payment_result

        except Exception as e:
            logger.error(f"Payment processing failed: {e}")
            raise

    async def _simulate_payment(
        self,
        from_pubkey: PublicKey,
        to_pubkey: PublicKey,
        lamports: int,
        metadata: Dict[str, Any]
    ) -> PaymentResult:
        """Simulate payment for development (replace with real implementation)"""

        # In production, this would:
        # 1. Create a transaction
        # 2. Request user signature
        # 3. Submit to network
        # 4. Wait for confirmation

        # For now, simulate successful payment
        fake_signature = f"fake_tx_{datetime.utcnow().isoformat()}"

        logger.info(
            f"Simulated payment: {lamports} lamports "
            f"from {from_pubkey} to {to_pubkey}"
        )

        return PaymentResult(
            transaction_signature=fake_signature,
            amount_sol=lamports / 1_000_000_000,
            from_wallet=str(from_pubkey),
            to_wallet=str(to_pubkey),
            block_height=1000,  # Fake block height
            timestamp=datetime.utcnow(),
            status="confirmed"
        )

    async def create_transfer_transaction(
        self,
        from_pubkey: PublicKey,
        to_pubkey: PublicKey,
        lamports: int
    ) -> Transaction:
        """Create a transfer transaction"""
        if not self.client:
            raise RuntimeError("Solana client not initialized")

        # Get recent blockhash
        recent_blockhash = await self.client.get_recent_blockhash()

        # Create transfer instruction
        transfer_instruction = transfer(
            TransferParams(
                from_pubkey=from_pubkey,
                to_pubkey=to_pubkey,
                lamports=lamports
            )
        )

        # Create transaction
        transaction = Transaction()
        transaction.add(transfer_instruction)
        transaction.recent_blockhash = recent_blockhash.value.blockhash

        return transaction

    async def get_balance(self, wallet_address: str) -> float:
        """Get wallet balance in SOL"""
        if not self.client:
            raise RuntimeError("Solana client not initialized")

        try:
            pubkey = PublicKey(wallet_address)
            balance_response = await self.client.get_balance(pubkey)
            lamports = balance_response.value
            return lamports / 1_000_000_000  # Convert to SOL
        except Exception as e:
            logger.error(f"Failed to get balance for {wallet_address}: {e}")
            return 0.0

    async def validate_wallet_address(self, address: str) -> bool:
        """Validate a Solana wallet address"""
        try:
            PublicKey(address)
            return True
        except Exception:
            return False

    async def distribute_training_rewards(
        self,
        participants: Dict[str, float],
        round_id: str
    ) -> Dict[str, PaymentResult]:
        """Distribute rewards to training participants"""
        results = {}

        for wallet_address, amount in participants.items():
            try:
                result = await self.process_payment(
                    from_wallet=str(self.treasury_keypair.public_key),
                    to_wallet=wallet_address,
                    amount=amount,
                    metadata={
                        "type": "training_reward",
                        "round_id": round_id
                    }
                )
                results[wallet_address] = result
                logger.info(f"Distributed {amount} SOL to {wallet_address}")

            except Exception as e:
                logger.error(f"Failed to distribute reward to {wallet_address}: {e}")

        return results

    async def get_transaction_status(self, signature: str) -> Optional[str]:
        """Get status of a transaction"""
        if not self.client:
            return None

        try:
            # For simulated payments, always return confirmed
            if signature.startswith("fake_tx_"):
                return "confirmed"

            # In production, query actual transaction status
            response = await self.client.get_signature_statuses([signature])
            if response.value and response.value[0]:
                return response.value[0].confirmation_status
            return None

        except Exception as e:
            logger.error(f"Failed to get transaction status: {e}")
            return None

    async def estimate_transaction_fee(
        self,
        from_wallet: str,
        to_wallet: str
    ) -> float:
        """Estimate transaction fee in SOL"""
        # Solana transactions typically cost ~0.000005 SOL
        return 0.000005