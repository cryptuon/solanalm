"""
Solana Payment Exceptions

Custom exceptions for payment processing errors.
"""

from typing import Optional


class SolanaPaymentError(Exception):
    """Base exception for all Solana payment errors"""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class InsufficientFundsError(SolanaPaymentError):
    """Wallet has insufficient SOL balance for transaction"""

    def __init__(
        self,
        wallet: str,
        required: float,
        available: float,
        include_fee: bool = True
    ):
        self.wallet = wallet
        self.required = required
        self.available = available
        self.include_fee = include_fee

        message = (
            f"Insufficient funds in wallet {wallet[:8]}...: "
            f"need {required:.6f} SOL (including fees), have {available:.6f} SOL"
        )
        super().__init__(message, {
            "wallet": wallet,
            "required_sol": required,
            "available_sol": available,
            "shortfall_sol": required - available
        })


class TransactionFailedError(SolanaPaymentError):
    """Transaction failed on-chain"""

    def __init__(self, signature: str, error: str, error_code: Optional[int] = None):
        self.signature = signature
        self.error = error
        self.error_code = error_code

        message = f"Transaction {signature[:16]}... failed: {error}"
        super().__init__(message, {
            "signature": signature,
            "error": error,
            "error_code": error_code
        })


class TransactionTimeoutError(SolanaPaymentError):
    """Transaction confirmation timed out"""

    def __init__(
        self,
        signature: str,
        timeout_seconds: int,
        last_status: Optional[str] = None
    ):
        self.signature = signature
        self.timeout_seconds = timeout_seconds
        self.last_status = last_status

        message = (
            f"Transaction {signature[:16]}... not confirmed "
            f"after {timeout_seconds} seconds"
        )
        super().__init__(message, {
            "signature": signature,
            "timeout_seconds": timeout_seconds,
            "last_status": last_status
        })


class BlockhashExpiredError(SolanaPaymentError):
    """Transaction blockhash has expired"""

    def __init__(self, signature: Optional[str] = None):
        self.signature = signature
        message = "Transaction blockhash expired - transaction needs to be rebuilt"
        super().__init__(message, {"signature": signature})


class InvalidWalletAddressError(SolanaPaymentError):
    """Invalid Solana wallet address format"""

    def __init__(self, address: str, reason: Optional[str] = None):
        self.address = address
        self.reason = reason

        message = f"Invalid wallet address: {address[:16]}..."
        if reason:
            message += f" ({reason})"

        super().__init__(message, {
            "address": address,
            "reason": reason
        })


class RateLimitError(SolanaPaymentError):
    """RPC rate limit exceeded"""

    def __init__(self, retry_after: Optional[int] = None):
        self.retry_after = retry_after

        message = "Solana RPC rate limit exceeded"
        if retry_after:
            message += f" - retry after {retry_after} seconds"

        super().__init__(message, {"retry_after": retry_after})


class NetworkError(SolanaPaymentError):
    """Network connectivity issue with Solana RPC"""

    def __init__(self, endpoint: str, original_error: Optional[str] = None):
        self.endpoint = endpoint
        self.original_error = original_error

        message = f"Failed to connect to Solana RPC: {endpoint}"
        if original_error:
            message += f" - {original_error}"

        super().__init__(message, {
            "endpoint": endpoint,
            "original_error": original_error
        })


class KeyStorageError(SolanaPaymentError):
    """Error accessing or managing keys"""

    def __init__(self, operation: str, reason: str):
        self.operation = operation
        self.reason = reason

        message = f"Key storage error during {operation}: {reason}"
        super().__init__(message, {
            "operation": operation,
            "reason": reason
        })


class SignatureVerificationError(SolanaPaymentError):
    """Transaction signature verification failed"""

    def __init__(self, signature: str, reason: Optional[str] = None):
        self.signature = signature
        self.reason = reason

        message = f"Signature verification failed for {signature[:16]}..."
        if reason:
            message += f": {reason}"

        super().__init__(message, {
            "signature": signature,
            "reason": reason
        })


class PaymentAlreadyProcessedError(SolanaPaymentError):
    """Payment has already been processed"""

    def __init__(self, payment_id: str, status: str):
        self.payment_id = payment_id
        self.status = status

        message = f"Payment {payment_id} already processed with status: {status}"
        super().__init__(message, {
            "payment_id": payment_id,
            "status": status
        })
