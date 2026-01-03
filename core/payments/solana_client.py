"""
Solana Payment Client

Handles SOL micro-transactions for inference requests and training rewards.
Supports both real transactions (testnet/mainnet) and simulated mode (development).
"""

import asyncio
import logging
import os
import random
from typing import Optional, Dict, Any, List
from datetime import datetime

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed, Finalized
from solders.keypair import Keypair
from solders.pubkey import Pubkey as PublicKey
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction
from solana.rpc.types import TxOpts

from core.models.schemas import PaymentRequest, PaymentResult
from core.config.settings import get_settings
from core.payments.wallet_manager import WalletManager
from core.payments.key_storage import get_key_storage
from core.payments.exceptions import (
    SolanaPaymentError,
    InsufficientFundsError,
    TransactionFailedError,
    TransactionTimeoutError,
    BlockhashExpiredError,
    InvalidWalletAddressError,
    NetworkError,
    RateLimitError
)

logger = logging.getLogger(__name__)


class SolanaPaymentClient:
    """
    Client for handling Solana payments.

    Supports two modes:
    - Development: Simulated payments (no real transactions)
    - Production: Real Solana transactions on testnet/mainnet

    Usage:
        client = SolanaPaymentClient()
        await client.initialize()

        result = await client.process_payment(
            from_wallet="...",
            to_wallet="...",
            amount=0.001
        )
    """

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        simulate_payments: Optional[bool] = None
    ):
        settings = get_settings()

        self.rpc_url = rpc_url or settings.solana_rpc_url
        self.network = settings.solana_network

        # Auto-detect simulation mode based on environment
        if simulate_payments is None:
            self.simulate_payments = settings.environment.value == "development"
        else:
            self.simulate_payments = simulate_payments

        # Transaction settings
        self.tx_timeout_seconds = settings.solana_tx_timeout_seconds
        self.tx_max_retries = settings.solana_tx_max_retries
        self.confirmation_commitment = settings.solana_tx_confirmation_commitment

        # Components
        self.client: Optional[AsyncClient] = None
        self.wallet_manager: Optional[WalletManager] = None

        # Payment tracking (will be moved to database)
        self.pending_payments: Dict[str, PaymentRequest] = {}
        self.payment_history: Dict[str, PaymentResult] = {}

        self._initialized = False

    @property
    def treasury_address(self) -> Optional[str]:
        """Get treasury wallet address"""
        if self.wallet_manager:
            return self.wallet_manager.treasury_address
        return None

    async def initialize(self) -> None:
        """Initialize the Solana payment client"""
        if self._initialized:
            logger.debug("Payment client already initialized")
            return

        logger.info(f"Initializing Solana payment client (network: {self.network})")

        # Initialize RPC client
        self.client = AsyncClient(self.rpc_url)

        # Check connection
        try:
            connected = await self.client.is_connected()
            if connected:
                logger.info(f"Connected to Solana RPC: {self.rpc_url}")
            else:
                raise NetworkError(self.rpc_url, "Connection check failed")
        except Exception as e:
            raise NetworkError(self.rpc_url, str(e))

        # Initialize wallet manager
        self.wallet_manager = WalletManager(rpc_url=self.rpc_url)
        await self.wallet_manager.initialize()

        if self.simulate_payments:
            logger.warning(
                "Payment simulation mode enabled. "
                "Set SOLANALM_ENVIRONMENT=testnet or mainnet for real transactions."
            )
        else:
            balance = await self.wallet_manager.get_treasury_balance()
            logger.info(f"Treasury balance: {balance:.6f} SOL")

        self._initialized = True
        logger.info("Solana payment client initialized successfully")

    async def close(self) -> None:
        """Close the Solana client and wallet manager"""
        if self.wallet_manager:
            await self.wallet_manager.close()
        if self.client:
            await self.client.close()
        self._initialized = False
        logger.info("Solana payment client closed")

    async def process_payment(
        self,
        from_wallet: str,
        to_wallet: str,
        amount: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentResult:
        """
        Process a payment between wallets.

        In development mode, simulates the payment.
        In production mode, executes a real Solana transaction.

        Args:
            from_wallet: Source wallet address
            to_wallet: Destination wallet address
            amount: Amount in SOL
            metadata: Optional metadata for the payment

        Returns:
            PaymentResult with transaction details
        """
        if not self._initialized:
            raise RuntimeError("Payment client not initialized")

        # Validate addresses
        if not WalletManager.validate_address(from_wallet):
            raise InvalidWalletAddressError(from_wallet, "Invalid source wallet")
        if not WalletManager.validate_address(to_wallet):
            raise InvalidWalletAddressError(to_wallet, "Invalid destination wallet")

        # Convert SOL to lamports
        lamports = int(amount * 1_000_000_000)

        if lamports <= 0:
            raise SolanaPaymentError("Payment amount must be positive")

        # Create public keys
        from_pubkey = PublicKey(from_wallet)
        to_pubkey = PublicKey(to_wallet)

        try:
            if self.simulate_payments:
                # Development mode - simulate payment
                result = await self._simulate_payment(
                    from_pubkey, to_pubkey, lamports, metadata or {}
                )
            else:
                # Production mode - real transaction
                result = await self._execute_real_payment(
                    from_pubkey, to_pubkey, lamports, metadata or {}
                )

            # Track payment
            self.payment_history[result.transaction_signature] = result

            return result

        except SolanaPaymentError:
            raise
        except Exception as e:
            logger.error(f"Payment processing failed: {e}")
            raise SolanaPaymentError(f"Payment failed: {e}")

    async def _simulate_payment(
        self,
        from_pubkey: PublicKey,
        to_pubkey: PublicKey,
        lamports: int,
        metadata: Dict[str, Any]
    ) -> PaymentResult:
        """Simulate payment for development mode"""
        # Generate fake signature
        fake_signature = f"sim_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"

        logger.info(
            f"[SIMULATED] Payment: {lamports / 1e9:.6f} SOL "
            f"from {str(from_pubkey)[:8]}... to {str(to_pubkey)[:8]}..."
        )

        # Simulate small delay
        await asyncio.sleep(0.1)

        return PaymentResult(
            transaction_signature=fake_signature,
            amount_sol=lamports / 1_000_000_000,
            from_wallet=str(from_pubkey),
            to_wallet=str(to_pubkey),
            block_height=1000 + random.randint(1, 1000),
            timestamp=datetime.utcnow(),
            status="confirmed"
        )

    async def _execute_real_payment(
        self,
        from_pubkey: PublicKey,
        to_pubkey: PublicKey,
        lamports: int,
        metadata: Dict[str, Any]
    ) -> PaymentResult:
        """
        Execute a real Solana transaction.

        For now, treasury pays on behalf of users (custodial model).
        Future: Support user-signed transactions.
        """
        if not self.wallet_manager or not self.wallet_manager.treasury_keypair:
            raise RuntimeError("Treasury wallet not initialized")

        # Check treasury balance
        await self.wallet_manager.ensure_sufficient_balance(
            amount_sol=lamports / 1_000_000_000,
            include_fee=True
        )

        # Build transaction
        transaction = await self._build_transfer_transaction(
            from_pubkey=self.wallet_manager.treasury_pubkey,  # Treasury pays
            to_pubkey=to_pubkey,
            lamports=lamports
        )

        # Sign with treasury keypair
        transaction.sign(self.wallet_manager.treasury_keypair)

        # Send with retry
        signature = await self._send_with_retry(transaction)

        # Wait for confirmation
        block_height = await self._wait_for_confirmation(signature)

        logger.info(
            f"Payment confirmed: {lamports / 1e9:.6f} SOL to {str(to_pubkey)[:8]}... "
            f"(tx: {signature[:16]}...)"
        )

        return PaymentResult(
            transaction_signature=signature,
            amount_sol=lamports / 1_000_000_000,
            from_wallet=str(self.wallet_manager.treasury_pubkey),
            to_wallet=str(to_pubkey),
            block_height=block_height,
            timestamp=datetime.utcnow(),
            status="confirmed"
        )

    async def _build_transfer_transaction(
        self,
        from_pubkey: PublicKey,
        to_pubkey: PublicKey,
        lamports: int
    ) -> Transaction:
        """Build a transfer transaction with recent blockhash"""
        if not self.client:
            raise RuntimeError("Solana client not initialized")

        # Get recent blockhash
        blockhash_response = await self.client.get_latest_blockhash(commitment=Confirmed)
        recent_blockhash = blockhash_response.value.blockhash

        # Create transfer instruction
        transfer_ix = transfer(
            TransferParams(
                from_pubkey=from_pubkey,
                to_pubkey=to_pubkey,
                lamports=lamports
            )
        )

        # Build transaction
        transaction = Transaction()
        transaction.add(transfer_ix)
        transaction.recent_blockhash = recent_blockhash
        transaction.fee_payer = from_pubkey

        return transaction

    async def _send_with_retry(
        self,
        transaction: Transaction,
        max_retries: Optional[int] = None
    ) -> str:
        """Send transaction with retry logic"""
        max_retries = max_retries or self.tx_max_retries
        last_error = None

        for attempt in range(max_retries):
            try:
                opts = TxOpts(
                    skip_preflight=False,
                    preflight_commitment=Confirmed
                )

                response = await self.client.send_transaction(
                    transaction,
                    self.wallet_manager.treasury_keypair,
                    opts=opts
                )

                if response.value:
                    return str(response.value)

                raise TransactionFailedError("unknown", "No signature returned")

            except Exception as e:
                last_error = e
                error_str = str(e).lower()

                # Non-retryable errors
                if "insufficient" in error_str:
                    raise InsufficientFundsError(
                        wallet=self.treasury_address or "unknown",
                        required=0,
                        available=0
                    )

                if "blockhash" in error_str and "expired" in error_str:
                    # Rebuild transaction with new blockhash
                    logger.warning("Blockhash expired, rebuilding transaction...")
                    transaction = await self._rebuild_transaction(transaction)
                    continue

                # Rate limiting
                if "429" in error_str or "rate" in error_str:
                    delay = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Rate limited, retrying in {delay:.1f}s...")
                    await asyncio.sleep(delay)
                    continue

                # Other errors - retry with backoff
                if attempt < max_retries - 1:
                    delay = (1.5 ** attempt) + random.uniform(0, 0.5)
                    logger.warning(f"Transaction failed, retrying in {delay:.1f}s: {e}")
                    await asyncio.sleep(delay)

        raise NetworkError(self.rpc_url, f"Failed after {max_retries} attempts: {last_error}")

    async def _rebuild_transaction(self, old_transaction: Transaction) -> Transaction:
        """Rebuild transaction with fresh blockhash"""
        # Get new blockhash
        blockhash_response = await self.client.get_latest_blockhash(commitment=Confirmed)

        # Create new transaction with same instructions
        new_transaction = Transaction()
        new_transaction.instructions = old_transaction.instructions
        new_transaction.recent_blockhash = blockhash_response.value.blockhash
        new_transaction.fee_payer = old_transaction.fee_payer

        return new_transaction

    async def _wait_for_confirmation(
        self,
        signature: str,
        timeout: Optional[int] = None
    ) -> int:
        """Wait for transaction confirmation and return block height"""
        timeout = timeout or self.tx_timeout_seconds
        start_time = asyncio.get_event_loop().time()
        last_status = None

        while (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                response = await self.client.get_signature_statuses([signature])

                if response.value and response.value[0]:
                    status = response.value[0]
                    last_status = status.confirmation_status

                    if status.err:
                        raise TransactionFailedError(
                            signature=signature,
                            error=str(status.err)
                        )

                    if status.confirmation_status in ["confirmed", "finalized"]:
                        # Get block height
                        tx_response = await self.client.get_transaction(
                            signature,
                            commitment=Confirmed
                        )
                        if tx_response.value:
                            return tx_response.value.slot
                        return 0

            except TransactionFailedError:
                raise
            except Exception as e:
                logger.debug(f"Status check error (will retry): {e}")

            await asyncio.sleep(1)

        raise TransactionTimeoutError(
            signature=signature,
            timeout_seconds=timeout,
            last_status=last_status
        )

    async def get_balance(self, wallet_address: str) -> float:
        """Get wallet balance in SOL"""
        if self.wallet_manager:
            return await self.wallet_manager.get_balance(wallet_address)

        if not self.client:
            raise RuntimeError("Solana client not initialized")

        try:
            pubkey = PublicKey(wallet_address)
            response = await self.client.get_balance(pubkey, commitment=Confirmed)
            return (response.value or 0) / 1_000_000_000
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return 0.0

    async def get_treasury_balance(self) -> float:
        """Get treasury wallet balance"""
        if self.wallet_manager:
            return await self.wallet_manager.get_treasury_balance()
        return 0.0

    async def validate_wallet_address(self, address: str) -> bool:
        """Validate a Solana wallet address"""
        return WalletManager.validate_address(address)

    async def distribute_training_rewards(
        self,
        participants: Dict[str, float],
        round_id: str
    ) -> Dict[str, PaymentResult]:
        """
        Distribute rewards to training participants.

        Args:
            participants: Dict mapping wallet_address -> reward_amount_sol
            round_id: Training round ID for tracking

        Returns:
            Dict mapping wallet_address -> PaymentResult
        """
        results = {}
        failed = []

        for wallet_address, amount in participants.items():
            try:
                result = await self.process_payment(
                    from_wallet=self.treasury_address or "",
                    to_wallet=wallet_address,
                    amount=amount,
                    metadata={
                        "type": "training_reward",
                        "round_id": round_id
                    }
                )
                results[wallet_address] = result
                logger.info(f"Distributed {amount:.6f} SOL reward to {wallet_address[:8]}...")

            except Exception as e:
                logger.error(f"Failed to distribute reward to {wallet_address[:8]}...: {e}")
                failed.append(wallet_address)

        if failed:
            logger.warning(f"Failed to distribute rewards to {len(failed)} participants")

        return results

    async def get_transaction_status(self, signature: str) -> Optional[str]:
        """Get status of a transaction"""
        if not self.client:
            return None

        # Handle simulated transactions
        if signature.startswith("sim_"):
            return "confirmed"

        try:
            response = await self.client.get_signature_statuses([signature])
            if response.value and response.value[0]:
                return response.value[0].confirmation_status
            return "unknown"
        except Exception as e:
            logger.error(f"Failed to get transaction status: {e}")
            return None

    async def estimate_transaction_fee(self) -> float:
        """Estimate transaction fee in SOL"""
        # Solana base fee is 5000 lamports per signature
        # Most transfers have 1 signature
        return 0.000005

    def get_status(self) -> dict:
        """Get payment client status"""
        return {
            "initialized": self._initialized,
            "network": self.network,
            "rpc_url": self.rpc_url,
            "simulate_payments": self.simulate_payments,
            "treasury_address": self.treasury_address,
            "wallet_manager": self.wallet_manager.get_status() if self.wallet_manager else None
        }
