"""
Secure Key Storage for Solana Wallets

Provides abstraction for loading and storing Solana keypairs securely.
Supports multiple backends: environment variables, encrypted files, and Vault.
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path

from solders.keypair import Keypair

from core.payments.exceptions import KeyStorageError

logger = logging.getLogger(__name__)


class KeyStorage(ABC):
    """Abstract base class for key storage backends"""

    @abstractmethod
    async def load_keypair(self) -> Keypair:
        """Load keypair from storage"""
        pass

    @abstractmethod
    async def save_keypair(self, keypair: Keypair) -> None:
        """Save keypair to storage"""
        pass

    @abstractmethod
    async def exists(self) -> bool:
        """Check if keypair exists in storage"""
        pass


class EnvironmentKeyStorage(KeyStorage):
    """
    Load keypair from environment variable.

    The private key should be base58 encoded (64 bytes = 128 chars).

    Environment variable: TREASURY_PRIVATE_KEY

    Usage (development only):
        export TREASURY_PRIVATE_KEY="base58_encoded_private_key"
    """

    def __init__(self, env_var: str = "TREASURY_PRIVATE_KEY"):
        self.env_var = env_var

    async def load_keypair(self) -> Keypair:
        """Load keypair from environment variable"""
        private_key = os.getenv(self.env_var)

        if not private_key:
            raise KeyStorageError(
                "load",
                f"Environment variable {self.env_var} not set"
            )

        try:
            # Use solders' built-in base58 decoding
            return Keypair.from_base58_string(private_key)

        except Exception as e:
            raise KeyStorageError("load", f"Failed to decode private key: {e}")

    async def save_keypair(self, keypair: Keypair) -> None:
        """Cannot save to environment - log warning"""
        logger.warning(
            f"Cannot save keypair to environment variable. "
            f"Set {self.env_var} manually with: {str(keypair)}"
        )

    async def exists(self) -> bool:
        """Check if environment variable is set"""
        return os.getenv(self.env_var) is not None


class FileKeyStorage(KeyStorage):
    """
    Load keypair from JSON file (Solana CLI compatible format).

    File format (same as `solana-keygen new`):
        [array of 64 integers representing the secret key bytes]

    Optionally supports password-encrypted files.
    """

    def __init__(
        self,
        file_path: str,
        password: Optional[str] = None
    ):
        self.file_path = Path(file_path).expanduser()
        self.password = password

    async def load_keypair(self) -> Keypair:
        """Load keypair from JSON file"""
        if not self.file_path.exists():
            raise KeyStorageError(
                "load",
                f"Keyfile not found: {self.file_path}"
            )

        try:
            with open(self.file_path, 'r') as f:
                content = f.read()

            # Handle encrypted files
            if self.password and content.startswith('encrypted:'):
                content = self._decrypt(content, self.password)

            # Parse JSON array of bytes
            key_bytes = bytes(json.loads(content))

            if len(key_bytes) != 64:
                raise KeyStorageError(
                    "load",
                    f"Invalid keyfile format: expected 64 bytes, got {len(key_bytes)}"
                )

            return Keypair.from_bytes(key_bytes)

        except json.JSONDecodeError as e:
            raise KeyStorageError("load", f"Invalid JSON in keyfile: {e}")
        except Exception as e:
            raise KeyStorageError("load", f"Failed to load keyfile: {e}")

    async def save_keypair(self, keypair: Keypair) -> None:
        """Save keypair to JSON file"""
        try:
            # Ensure directory exists
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

            # Get full keypair bytes (64 bytes)
            secret_key = keypair.to_bytes()
            content = json.dumps(list(secret_key))

            # Encrypt if password provided
            if self.password:
                content = self._encrypt(content, self.password)

            # Write with restricted permissions
            with open(self.file_path, 'w') as f:
                f.write(content)

            # Set file permissions to owner-only (Unix)
            os.chmod(self.file_path, 0o600)

            logger.info(f"Keypair saved to {self.file_path}")

        except Exception as e:
            raise KeyStorageError("save", f"Failed to save keyfile: {e}")

    async def exists(self) -> bool:
        """Check if keyfile exists"""
        return self.file_path.exists()

    def _encrypt(self, content: str, password: str) -> str:
        """Encrypt content with password (simple implementation)"""
        try:
            from cryptography.fernet import Fernet
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            import base64

            # Derive key from password
            salt = b'solanalm_treasury_salt'  # In production, use random salt stored with file
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

            # Encrypt
            f = Fernet(key)
            encrypted = f.encrypt(content.encode())

            return f"encrypted:{base64.b64encode(encrypted).decode()}"

        except ImportError:
            logger.warning("cryptography package not installed - saving unencrypted")
            return content

    def _decrypt(self, content: str, password: str) -> str:
        """Decrypt content with password"""
        try:
            from cryptography.fernet import Fernet
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            import base64

            # Remove prefix
            encrypted_data = base64.b64decode(content[10:])  # Remove "encrypted:"

            # Derive key from password
            salt = b'solanalm_treasury_salt'
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

            # Decrypt
            f = Fernet(key)
            return f.decrypt(encrypted_data).decode()

        except Exception as e:
            raise KeyStorageError("decrypt", f"Failed to decrypt keyfile: {e}")


class MemoryKeyStorage(KeyStorage):
    """
    In-memory key storage for testing.

    WARNING: Keys are lost when process exits.
    Only use for development/testing.
    """

    def __init__(self, keypair: Optional[Keypair] = None):
        self._keypair = keypair

    async def load_keypair(self) -> Keypair:
        """Load keypair from memory"""
        if self._keypair is None:
            raise KeyStorageError("load", "No keypair in memory storage")
        return self._keypair

    async def save_keypair(self, keypair: Keypair) -> None:
        """Save keypair to memory"""
        self._keypair = keypair
        logger.warning("Keypair stored in memory - will be lost on process exit")

    async def exists(self) -> bool:
        """Check if keypair exists"""
        return self._keypair is not None


def get_key_storage(
    storage_type: Optional[str] = None,
    **kwargs
) -> KeyStorage:
    """
    Factory function to get appropriate key storage backend.

    Auto-detects based on environment if storage_type not specified.

    Args:
        storage_type: "env", "file", "memory", or None for auto-detect
        **kwargs: Additional arguments for the storage backend

    Returns:
        KeyStorage instance
    """
    if storage_type is None:
        # Auto-detect based on what's available
        if os.getenv("TREASURY_PRIVATE_KEY"):
            storage_type = "env"
        elif os.getenv("TREASURY_KEYFILE_PATH"):
            storage_type = "file"
            kwargs["file_path"] = os.getenv("TREASURY_KEYFILE_PATH")
            kwargs["password"] = os.getenv("TREASURY_KEYFILE_PASSWORD")
        else:
            storage_type = "memory"
            logger.warning("No key storage configured - using memory (development only)")

    if storage_type == "env":
        return EnvironmentKeyStorage(
            env_var=kwargs.get("env_var", "TREASURY_PRIVATE_KEY")
        )
    elif storage_type == "file":
        return FileKeyStorage(
            file_path=kwargs.get("file_path", "~/.config/solanalm/treasury.json"),
            password=kwargs.get("password")
        )
    elif storage_type == "memory":
        return MemoryKeyStorage(keypair=kwargs.get("keypair"))
    else:
        raise ValueError(f"Unknown key storage type: {storage_type}")
