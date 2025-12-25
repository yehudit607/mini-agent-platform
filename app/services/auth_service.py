from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import AuthenticationError
from app.logging_config import setup_logger
from app.models.api_key import APIKey
from app.repositories.api_key_repository import APIKeyRepository

logger = setup_logger(__name__)


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = APIKeyRepository(session)

    async def validate_api_key(self, plain_key: str) -> UUID:
        """
        Validate API key and return tenant_id.
        Updates last_used_at timestamp on successful validation.
        """
        key_hash = APIKey.hash_key(plain_key)
        api_key = await self.repository.get_by_hash(key_hash)

        if api_key is None:
            logger.warning(f"Failed authentication attempt with invalid API key")
            raise AuthenticationError(
                error_code="INVALID_API_KEY",
                message="Invalid API key",
            )

        if not api_key.is_active:
            logger.warning(
                f"Authentication attempt with inactive API key: {api_key.key_prefix}"
            )
            raise AuthenticationError(
                error_code="API_KEY_INACTIVE",
                message="API key has been deactivated",
            )

        if api_key.tenant and not api_key.tenant.is_active:
            logger.warning(
                f"Authentication attempt for inactive tenant: {api_key.tenant_id}"
            )
            raise AuthenticationError(
                error_code="TENANT_INACTIVE",
                message="Tenant account has been deactivated",
            )

        await self.repository.update_last_used(api_key.id)

        logger.info(
            f"Successful authentication for tenant_id={api_key.tenant_id}, "
            f"key_prefix={api_key.key_prefix}"
        )

        return api_key.tenant_id
