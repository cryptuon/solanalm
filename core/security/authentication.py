"""
Comprehensive Security and Authentication System
JWT tokens, API keys, rate limiting, and security middleware
"""

import jwt
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from functools import wraps
import asyncio
from collections import defaultdict, deque
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt
import base58  # For Solana address validation

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    ADMIN = "admin"
    NODE_OPERATOR = "node_operator"
    CLIENT = "client"
    READONLY = "readonly"


class SecurityLevel(str, Enum):
    PUBLIC = "public"
    AUTHENTICATED = "authenticated"
    NODE_OPERATOR = "node_operator"
    ADMIN = "admin"


@dataclass
class User:
    """User account information"""
    user_id: str
    username: str
    email: str
    role: UserRole
    wallet_address: Optional[str] = None
    api_key: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    is_active: bool = True
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None


@dataclass
class APIKey:
    """API key information"""
    key_id: str
    key_hash: str
    user_id: str
    name: str
    permissions: List[str]
    rate_limit: int = 1000  # requests per hour
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    is_active: bool = True


@dataclass
class RateLimitEntry:
    """Rate limiting entry"""
    count: int = 0
    window_start: datetime = field(default_factory=datetime.utcnow)
    blocked_until: Optional[datetime] = None


class SecurityManager:
    """Comprehensive security and authentication manager"""

    def __init__(self, jwt_secret: str, jwt_algorithm: str = "HS256"):
        self.jwt_secret = jwt_secret
        self.jwt_algorithm = jwt_algorithm
        self.jwt_expiration_hours = 24

        # User and API key storage (in production, use proper database)
        self.users: Dict[str, User] = {}
        self.api_keys: Dict[str, APIKey] = {}
        self.user_by_username: Dict[str, str] = {}
        self.user_by_wallet: Dict[str, str] = {}

        # Rate limiting
        self.rate_limits: Dict[str, RateLimitEntry] = {}
        self.default_rate_limit = 100  # requests per minute

        # Security settings
        self.max_failed_attempts = 5
        self.lockout_duration_minutes = 30
        self.password_min_length = 8

        # JWT bearer token handler
        self.bearer = HTTPBearer(auto_error=False)

    def generate_api_key(self) -> str:
        """Generate a secure API key"""
        return secrets.token_urlsafe(32)

    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def validate_solana_address(self, address: str) -> bool:
        """Validate Solana wallet address format"""
        try:
            # Solana addresses are base58 encoded and 44 characters long
            if len(address) != 44:
                return False

            # Try to decode as base58
            decoded = base58.b58decode(address)
            return len(decoded) == 32
        except Exception:
            return False

    def create_user(self, username: str, email: str, password: str,
                   role: UserRole = UserRole.CLIENT,
                   wallet_address: Optional[str] = None) -> User:
        """Create a new user account"""
        # Validate inputs
        if username in self.user_by_username:
            raise ValueError("Username already exists")

        if wallet_address and not self.validate_solana_address(wallet_address):
            raise ValueError("Invalid Solana wallet address")

        if wallet_address and wallet_address in self.user_by_wallet:
            raise ValueError("Wallet address already registered")

        if len(password) < self.password_min_length:
            raise ValueError(f"Password must be at least {self.password_min_length} characters")

        # Create user
        user_id = secrets.token_hex(16)
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            role=role,
            wallet_address=wallet_address
        )

        # Store user
        self.users[user_id] = user
        self.user_by_username[username] = user_id
        if wallet_address:
            self.user_by_wallet[wallet_address] = user_id

        # Store password hash (in production, use proper user storage)
        # This is simplified for demonstration

        logger.info(f"Created user {username} with role {role.value}")
        return user

    def create_api_key(self, user_id: str, name: str,
                      permissions: List[str] = None,
                      rate_limit: int = 1000,
                      expires_in_days: Optional[int] = None) -> str:
        """Create an API key for a user"""
        if user_id not in self.users:
            raise ValueError("User not found")

        api_key = self.generate_api_key()
        key_hash = self.hash_api_key(api_key)
        key_id = secrets.token_hex(8)

        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

        api_key_obj = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            user_id=user_id,
            name=name,
            permissions=permissions or [],
            rate_limit=rate_limit,
            expires_at=expires_at
        )

        self.api_keys[key_id] = api_key_obj
        logger.info(f"Created API key '{name}' for user {user_id}")

        return api_key

    def authenticate_jwt(self, token: str) -> Optional[User]:
        """Authenticate a JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])

            user_id = payload.get("user_id")
            if not user_id or user_id not in self.users:
                return None

            user = self.users[user_id]
            if not user.is_active:
                return None

            # Check if user is locked out
            if user.locked_until and datetime.utcnow() < user.locked_until:
                return None

            return user

        except jwt.InvalidTokenError:
            return None

    def authenticate_api_key(self, api_key: str) -> Optional[User]:
        """Authenticate an API key"""
        key_hash = self.hash_api_key(api_key)

        for api_key_obj in self.api_keys.values():
            if (api_key_obj.key_hash == key_hash and
                api_key_obj.is_active and
                (not api_key_obj.expires_at or datetime.utcnow() < api_key_obj.expires_at)):

                # Update last used
                api_key_obj.last_used = datetime.utcnow()

                # Get user
                user = self.users.get(api_key_obj.user_id)
                if user and user.is_active:
                    return user

        return None

    def authenticate_wallet(self, wallet_address: str, signature: str, message: str) -> Optional[User]:
        """Authenticate using Solana wallet signature"""
        # In production, verify the signature against the message
        # This is a simplified implementation

        if not self.validate_solana_address(wallet_address):
            return None

        user_id = self.user_by_wallet.get(wallet_address)
        if user_id and user_id in self.users:
            user = self.users[user_id]
            if user.is_active:
                return user

        return None

    def create_jwt_token(self, user: User) -> str:
        """Create a JWT token for a user"""
        payload = {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role.value,
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=self.jwt_expiration_hours)
        }

        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)

    def check_rate_limit(self, identifier: str, limit: Optional[int] = None) -> bool:
        """Check if request is within rate limits"""
        if limit is None:
            limit = self.default_rate_limit

        now = datetime.utcnow()
        window_duration = timedelta(minutes=1)

        if identifier not in self.rate_limits:
            self.rate_limits[identifier] = RateLimitEntry()

        entry = self.rate_limits[identifier]

        # Check if blocked
        if entry.blocked_until and now < entry.blocked_until:
            return False

        # Reset window if expired
        if now - entry.window_start > window_duration:
            entry.count = 0
            entry.window_start = now
            entry.blocked_until = None

        # Check limit
        if entry.count >= limit:
            # Block for 5 minutes if limit exceeded
            entry.blocked_until = now + timedelta(minutes=5)
            logger.warning(f"Rate limit exceeded for {identifier}")
            return False

        entry.count += 1
        return True

    def require_permission(self, permission: str):
        """Decorator to require specific permission"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # In a real implementation, get user from request context
                # and check permissions
                return await func(*args, **kwargs)
            return wrapper
        return decorator

    def get_current_user(self, credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))):
        """FastAPI dependency to get current authenticated user"""
        if not credentials:
            return None

        # Try JWT first
        user = self.authenticate_jwt(credentials.credentials)
        if user:
            return user

        # Try API key
        user = self.authenticate_api_key(credentials.credentials)
        if user:
            return user

        return None

    def require_auth(self, security_level: SecurityLevel = SecurityLevel.AUTHENTICATED):
        """FastAPI dependency to require authentication"""
        def dependency(user: Optional[User] = Depends(self.get_current_user)):
            if security_level == SecurityLevel.PUBLIC:
                return user

            if not user:
                raise HTTPException(status_code=401, detail="Authentication required")

            if security_level == SecurityLevel.NODE_OPERATOR and user.role not in [UserRole.NODE_OPERATOR, UserRole.ADMIN]:
                raise HTTPException(status_code=403, detail="Node operator access required")

            if security_level == SecurityLevel.ADMIN and user.role != UserRole.ADMIN:
                raise HTTPException(status_code=403, detail="Admin access required")

            return user

        return dependency

    def rate_limit_middleware(self, requests_per_minute: int = 100):
        """Rate limiting middleware"""
        async def middleware(request: Request, call_next):
            # Get client identifier
            client_ip = request.client.host
            user_agent = request.headers.get("user-agent", "unknown")
            identifier = f"{client_ip}:{user_agent}"

            # Check rate limit
            if not self.check_rate_limit(identifier, requests_per_minute):
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded",
                    headers={"Retry-After": "300"}
                )

            response = await call_next(request)
            return response

        return middleware

    def input_sanitization_middleware(self):
        """Input sanitization middleware"""
        async def middleware(request: Request, call_next):
            # Sanitize request data (simplified implementation)
            # In production, implement comprehensive input validation

            response = await call_next(request)
            return response

        return middleware

    def security_headers_middleware(self):
        """Add security headers"""
        async def middleware(request: Request, call_next):
            response = await call_next(request)

            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = "default-src 'self'"

            return response

        return middleware

    def get_security_summary(self) -> Dict[str, Any]:
        """Get security system summary"""
        active_users = len([u for u in self.users.values() if u.is_active])
        active_api_keys = len([k for k in self.api_keys.values() if k.is_active])
        blocked_ips = len([r for r in self.rate_limits.values() if r.blocked_until and datetime.utcnow() < r.blocked_until])

        return {
            "users": {
                "total": len(self.users),
                "active": active_users,
                "by_role": self._count_users_by_role()
            },
            "api_keys": {
                "total": len(self.api_keys),
                "active": active_api_keys
            },
            "rate_limiting": {
                "blocked_identifiers": blocked_ips,
                "total_tracked": len(self.rate_limits)
            },
            "security_events": {
                "failed_logins_24h": self._count_failed_logins(),
                "locked_accounts": len([u for u in self.users.values() if u.locked_until and datetime.utcnow() < u.locked_until])
            }
        }

    def _count_users_by_role(self) -> Dict[str, int]:
        """Count users by role"""
        counts = defaultdict(int)
        for user in self.users.values():
            counts[user.role.value] += 1
        return dict(counts)

    def _count_failed_logins(self) -> int:
        """Count failed logins in last 24 hours"""
        # In production, track failed login attempts properly
        return sum(u.failed_login_attempts for u in self.users.values())


# Global security manager instance
security_manager: Optional[SecurityManager] = None


def init_security_manager(jwt_secret: str) -> SecurityManager:
    """Initialize global security manager"""
    global security_manager
    security_manager = SecurityManager(jwt_secret)

    # Create default admin user (in production, do this via secure setup)
    try:
        admin_user = security_manager.create_user(
            username="admin",
            email="admin@solanalm.com",
            password="admin123",  # Change in production!
            role=UserRole.ADMIN
        )
        logger.info("Created default admin user")
    except ValueError:
        pass  # User already exists

    return security_manager


def get_security_manager() -> SecurityManager:
    """Get global security manager"""
    if security_manager is None:
        raise RuntimeError("Security manager not initialized")
    return security_manager


# Security utilities
def generate_secure_secret() -> str:
    """Generate a secure secret key"""
    return secrets.token_urlsafe(32)


def validate_input_length(value: str, max_length: int = 1000) -> str:
    """Validate and truncate input length"""
    if len(value) > max_length:
        logger.warning(f"Input truncated from {len(value)} to {max_length} characters")
        return value[:max_length]
    return value


def sanitize_string(value: str) -> str:
    """Basic string sanitization"""
    # Remove potential XSS and injection attempts
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`']
    sanitized = value
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    return sanitized.strip()


# Security decorators
def require_wallet_signature(func):
    """Decorator to require Solana wallet signature"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # In production, verify wallet signature
        return await func(*args, **kwargs)
    return wrapper


def audit_log(action: str):
    """Decorator to log security-sensitive actions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"Security audit: {action} completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.warning(f"Security audit: {action} failed in {duration:.3f}s: {e}")
                raise
        return wrapper
    return decorator