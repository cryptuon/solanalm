"""
Base Repository Pattern

Provides common CRUD operations for all repositories.
"""

from typing import TypeVar, Generic, List, Optional, Type, Any
from sqlalchemy import select, delete, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository with common CRUD operations.

    Usage:
        class UserRepository(BaseRepository[UserModel]):
            def __init__(self, session: AsyncSession):
                super().__init__(session, UserModel)
    """

    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self.session = session
        self.model = model

    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """Get entity by primary key ID"""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[ModelType]:
        """Get all entities with pagination"""
        result = await self.session.execute(
            select(self.model).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        """Get total count of entities"""
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar() or 0

    async def create(self, obj: ModelType) -> ModelType:
        """Create a new entity"""
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def create_many(self, objects: List[ModelType]) -> List[ModelType]:
        """Create multiple entities"""
        self.session.add_all(objects)
        await self.session.flush()
        for obj in objects:
            await self.session.refresh(obj)
        return objects

    async def update(self, obj: ModelType) -> ModelType:
        """Update an existing entity"""
        merged = await self.session.merge(obj)
        await self.session.flush()
        return merged

    async def delete(self, id: Any) -> bool:
        """Delete entity by ID"""
        result = await self.session.execute(
            delete(self.model).where(self.model.id == id)
        )
        return result.rowcount > 0

    async def delete_obj(self, obj: ModelType) -> None:
        """Delete entity object"""
        await self.session.delete(obj)
        await self.session.flush()

    async def exists(self, id: Any) -> bool:
        """Check if entity exists"""
        result = await self.session.execute(
            select(func.count()).select_from(self.model).where(self.model.id == id)
        )
        return (result.scalar() or 0) > 0
