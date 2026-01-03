"""
Wallet Manager for SolanaLM

Manages treasury wallet and provides wallet operations for the payment system.
"""

import logging
from typing import Optional
from datetime import datetime

from solders.keypair import Keypair
from solders.pubkey import Pubkey as PublicKey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed

from core.payments.key_storage import KeyStorage, get_key_storage
from core.payments.exceptions import (
    InsufficientFundsError,
    NetworkError,
    KeyStorageError
)
from core.config.settings import get_settings

logger = logging.getLogger(__name__)


class WalletManager:
    """
    Manages Solana wallet operations for the SolanaLM treasury.

    Responsibilities:
    - Load and manage treasury keypair
    - Check wallet balances
    - Request airdrops (devnet/testnet only)
    - Validate wallet addresses

    Usage:
        wallet_manager = WalletManager()
        await wallet_manager.initialize()

        balance = await wallet_manager.get_treasury_balance()
        print(f"Treasury balance: {balance} SOL")
    """

    def __init__(
        self,
        rpc_url: Optional[str] = None,
        key_storage: Optional[KeyStorage] = None
    ):
        settings = get_settings()

        self.rpc_url = rpc_url or settings.solana_rpc_url
        self.network = settings.solana_network
        self.key_storage = key_storage or get_key_storage()

        self.client: Optional[AsyncClient] = None
        self.treasury_keypair: Optional[Keypair] = None
        self._initialized = False

    @property
    def treasury_pubkey(self) -> Optional[PublicKey]:
        """Get treasury public key"""
        if self.treasury_keypair:
            return self.treasury_keypair.pubkey()
        return None

    @property
    def treasury_address(self) -> Optional[str]:
        """Get treasury wallet address as string"""
        if self.treasury_pubkey:
            return str(self.treasury_pubkey)
        return None

    async def initialize(self) -> None:
        """Initialize wallet manager with RPC client and treasury keypair"""
        if self._initialized:
            logger.debug("Wallet manager already initialized")
            return

        # Initialize RPC client
        self.client = AsyncClient(self.rpc_url)

        # Test connection
        try:
            await self.client.is_connected()
            logger.info(f"Connected to Solana RPC: {self.rpc_url}")
        except Exception as e:
            raise NetworkError(self.rpc_url, str(e))

        # Load or create treasury keypair
        await self._load_treasury_keypair()

        self._initialized = True
        logger.info(f"Wallet manager initialized. Treasury: {self.treasury_address[:16]}...")

    async def _load_treasury_keypair(self) -> None:
        """Load treasury keypair from storage or create new one"""
        try:
            if await self.key_storage.exists():
                self.treasury_keypair = await self.key_storage.load_keypair()
                logger.info(f"Loaded existing treasury keypair: {self.treasury_address[:16]}...")
            else:
                # Create new keypair
                self.treasury_keypair = Keypair()
                await self.key_storage.save_keypair(self.treasury_keypair)
                logger.warning(
                    f"Created new treasury keypair: {self.treasury_address}\n"
                    f"IMPORTANT: Fund this wallet before processing payments!"
                )

                # Request airdrop on devnet/testnet
                if self.network in ["devnet", "testnet"]:
                    await self.request_airdrop(2.0)

        except KeyStorageError:
            raise
        except Exception as e:
            raise KeyStorageError("initialize", f"Failed to load treasury keypair: {e}")

    async def close(self) -> None:
        """Close RPC connection"""
        if self.client:
            await self.client.close()
            self._initialized = False
            logger.info("Wallet manager closed")

    async def get_balance(self, wallet_address: str) -> float:
        """
        Get wallet balance in SOL.

        Args:
            wallet_address: Solana wallet address

        Returns:
            Balance in SOL
        """
        if not self.client:
            raise RuntimeError("Wallet manager not initialized")

        try:
            pubkey = PublicKey(wallet_address)
            response = await self.client.get_balance(pubkey, commitment=Confirmed)

            if response.value is not None:
                return response.value / 1_000_000_000  # lamports to SOL
            return 0.0

        except Exception as e:
            logger.error(f"Failed to get balance for {wallet_address[:16]}...: {e}")
            return 0.0

    async def get_treasury_balance(self) -> float:
        """Get treasury wallet balance in SOL"""
        if not self.treasury_address:
            raise RuntimeError("Treasury not initialized")
        return await self.get_balance(self.treasury_address)

    async def ensure_sufficient_balance(
        self,
        amount_sol: float,
        include_fee: bool = True
    ) -> None:
        """
        Ensure treasury has sufficient balance for transaction.

        Args:
            amount_sol: Amount needed in SOL
            include_fee: Whether to include estimated transaction fee

        Raises:
            InsufficientFundsError: If balance is insufficient
        """
        fee_estimate = 0.000005 if include_fee else 0  # ~5000 lamports
        required = amount_sol + fee_estimate

        balance = await self.get_treasury_balance()

        if balance < required:
            raise InsufficientFundsError(
                wallet=self.treasury_address,
                required=required,
                available=balance,
                include_fee=include_fee
            )

    async def request_airdrop(self, amount_sol: float = 1.0) -> Optional[str]:
        """
        Request SOL airdrop (devnet/testnet only).

        Args:
            amount_sol: Amount to request (max 2 SOL per request)

        Returns:
            Transaction signature or None if failed
        """
        if self.network not in ["devnet", "testnet"]:
            logger.warning(f"Airdrop not available on {self.network}")
            return None

        if not self.treasury_pubkey or not self.client:
            raise RuntimeError("Wallet manager not initialized")

        try:
            lamports = int(min(amount_sol, 2.0) * 1_000_000_000)

            response = await self.client.request_airdrop(
                self.treasury_pubkey,
                lamports,
                commitment=Confirmed
            )

            if response.value:
                signature = str(response.value)
                logger.info(
                    f"Airdrop requested: {amount_sol} SOL to {self.treasury_address[:16]}...\n"
                    f"Signature: {signature}"
                )

                # Wait for confirmation
                await self._wait_for_confirmation(signature)

                new_balance = await self.get_treasury_balance()
                logger.info(f"New treasury balance: {new_balance} SOL")

                return signature

            return None

        except Exception as e:
            logger.error(f"Airdrop failed: {e}")
            return None

    async def _wait_for_confirmation(
        self,
        signature: str,
        max_attempts: int = 30
    ) -> bool:
        """Wait for transaction confirmation"""
        import asyncio

        for attempt in range(max_attempts):
            try:
                response = await self.client.get_signature_statuses([signature])

                if response.value and response.value[0]:
                    status = response.value[0]
                    if status.confirmation_status in ["confirmed", "finalized"]:
                        return True
                    if status.err:
                        logger.error(f"Transaction failed: {status.err}")
                        return False

            except Exception as e:
                logger.debug(f"Status check attempt {attempt + 1} failed: {e}")

            await asyncio.sleep(1)

        return False

    @staticmethod
    def validate_address(address: str) -> bool:
        """
        Validate Solana wallet address format.

        Args:
            address: Address to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            if not address or len(address) < 32 or len(address) > 44:
                return False

            # Try to create PublicKey - will raise if invalid
            PublicKey(address)
            return True

        except Exception:
            return False

    @staticmethod
    def generate_keypair() -> tuple[Keypair, str]:
        """
        Generate a new random keypair.

        Returns:
            Tuple of (Keypair, public_key_string)
        """
        keypair = Keypair()
        return keypair, str(keypair.pubkey())

    def get_status(self) -> dict:
        """Get wallet manager status"""
        return {
            "initialized": self._initialized,
            "network": self.network,
            "rpc_url": self.rpc_url,
            "treasury_address": self.treasury_address,
            "key_storage_type": type(self.key_storage).__name__
        }
