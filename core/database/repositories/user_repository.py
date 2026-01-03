"""
User Repository

Database operations for users and API keys.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.repositories.base import BaseRepository
from core.database.models.user import UserModel, APIKeyModel


class UserRepository(BaseRepository[UserModel]):
    """Repository for user operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, UserModel)

    async def get_by_user_id(self, user_id: str) -> Optional[UserModel]:
        """Get user by user_id"""
        result = await self.session.execute(
            select(UserModel).where(UserModel.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[UserModel]:
        """Get user by username"""
        result = await self.session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[UserModel]:
        """Get user by email"""
        result = await self.session.execute(
            select(UserModel).where(UserModel.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_wallet(self, wallet_address: str) -> Optional[UserModel]:
        """Get user by wallet address"""
        result = await self.session.execute(
            select(UserModel).where(UserModel.wallet_address == wallet_address)
        )
        return result.scalar_one_or_none()

    async def find_users_by_role(self, role: str) -> List[UserModel]:
        """Find all users with a specific role"""
        result = await self.session.execute(
            select(UserModel).where(UserModel.role == role)
        )
        return list(result.scalars().all())

    async def get_active_users(self) -> List[UserModel]:
        """Get all active users"""
        result = await self.session.execute(
            select(UserModel).where(UserModel.is_active == True)
        )
        return list(result.scalars().all())

    async def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp"""
        user = await self.get_by_user_id(user_id)
        if user:
            user.last_login = datetime.utcnow()
            user.failed_login_attempts = 0
            await self.session.flush()

    async def record_failed_login(self, user_id: str) -> int:
        """Record failed login attempt, return attempt count"""
        user = await self.get_by_user_id(user_id)
        if user:
            user.failed_login_attempts += 1
            await self.session.flush()
            return user.failed_login_attempts
        return 0

    async def lock_user(self, user_id: str, until: datetime) -> None:
        """Lock user account until specified time"""
        user = await self.get_by_user_id(user_id)
        if user:
            user.locked_until = until
            await self.session.flush()

    async def unlock_user(self, user_id: str) -> None:
        """Unlock user account"""
        user = await self.get_by_user_id(user_id)
        if user:
            user.locked_until = None
            user.failed_login_attempts = 0
            await self.session.flush()


class APIKeyRepository(BaseRepository[APIKeyModel]):
    """Repository for API key operations"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, APIKeyModel)

    async def get_by_key_id(self, key_id: str) -> Optional[APIKeyModel]:
        """Get API key by key_id"""
        result = await self.session.execute(
            select(APIKeyModel).where(APIKeyModel.key_id == key_id)
        )
        return result.scalar_one_or_none()

    async def get_by_key_hash(self, key_hash: str) -> Optional[APIKeyModel]:
        """Get API key by hash"""
        result = await self.session.execute(
            select(APIKeyModel).where(APIKeyModel.key_hash == key_hash)
        )
        return result.scalar_one_or_none()

    async def find_keys_by_user(self, user_id: str) -> List[APIKeyModel]:
        """Find all API keys for a user"""
        result = await self.session.execute(
            select(APIKeyModel).where(APIKeyModel.user_id == user_id)
        )
        return list(result.scalars().all())

    async def find_active_keys_by_user(self, user_id: str) -> List[APIKeyModel]:
        """Find all active API keys for a user"""
        result = await self.session.execute(
            select(APIKeyModel).where(
                and_(
                    APIKeyModel.user_id == user_id,
                    APIKeyModel.is_active == True
                )
            )
        )
        return list(result.scalars().all())

    async def update_last_used(self, key_id: str) -> None:
        """Update last used timestamp"""
        key = await self.get_by_key_id(key_id)
        if key:
            key.last_used = datetime.utcnow()
            key.total_requests += 1
            await self.session.flush()

    async def deactivate_key(self, key_id: str) -> bool:
        """Deactivate an API key"""
        key = await self.get_by_key_id(key_id)
        if key:
            key.is_active = False
            await self.session.flush()
            return True
        return False

    async def validate_key(self, key_hash: str) -> Optional[APIKeyModel]:
        """Validate API key and return if valid"""
        key = await self.get_by_key_hash(key_hash)
        if key and key.is_valid:
            await self.update_last_used(key.key_id)
            return key
        return None
