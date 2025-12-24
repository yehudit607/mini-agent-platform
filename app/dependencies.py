from typing import Optional
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.exceptions import AuthenticationError
from app.services.auth_service import AuthService


def get_auth_service(
    session: AsyncSession = Depends(get_async_session),
) -> AuthService:
    return AuthService(session)


async def get_current_tenant(
    x_api_key: Optional[str] = Header(None, alias="X-API-KEY"),
    auth_service: AuthService = Depends(get_auth_service),
) -> UUID:
    if x_api_key is None:
        raise AuthenticationError(
            error_code="MISSING_API_KEY",
            message="X-API-KEY header is required",
        )

    return await auth_service.validate_api_key(x_api_key)
