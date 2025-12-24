from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.api_key import APIKey
from app.models.tenant import Tenant


class APIKeyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_hash(self, key_hash: str) -> Optional[APIKey]:
        statement = (
            select(APIKey)
            .options(selectinload(APIKey.tenant))
            .where(APIKey.key_hash == key_hash)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def update_last_used(self, key_id: UUID) -> None:
        statement = select(APIKey).where(APIKey.id == key_id)
        result = await self.session.execute(statement)
        api_key = result.scalar_one_or_none()
        if api_key:
            api_key.last_used_at = datetime.utcnow()
            await self.session.flush()

    async def create(
        self, tenant_id: UUID, name: str
    ) -> Tuple[APIKey, str]:
        """
        Create a new API key.
        Returns: (APIKey entity, plain_key)
        Note: plain_key is only available at creation time.
        """
        plain_key, key_hash, key_prefix = APIKey.generate_key()

        api_key = APIKey(
            tenant_id=tenant_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
        )
        self.session.add(api_key)
        await self.session.flush()
        await self.session.refresh(api_key)

        return api_key, plain_key

    async def create_with_known_key(
        self, tenant_id: UUID, name: str, plain_key: str
    ) -> APIKey:
        """Create API key with a known plain key (for seeding demo keys)."""
        key_hash = APIKey.hash_key(plain_key)
        key_prefix = plain_key[:12] if len(plain_key) >= 12 else plain_key

        api_key = APIKey(
            tenant_id=tenant_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
        )
        self.session.add(api_key)
        await self.session.flush()
        await self.session.refresh(api_key)

        return api_key

    async def deactivate(self, key_id: UUID) -> bool:
        statement = select(APIKey).where(APIKey.id == key_id)
        result = await self.session.execute(statement)
        api_key = result.scalar_one_or_none()
        if api_key:
            api_key.is_active = False
            await self.session.flush()
            return True
        return False

    async def list_by_tenant(self, tenant_id: UUID) -> list[APIKey]:
        statement = select(APIKey).where(APIKey.tenant_id == tenant_id)
        result = await self.session.execute(statement)
        return list(result.scalars().all())
