from typing import Optional
from uuid import UUID

from fastapi import Depends, Header

from app.exceptions import AuthenticationError
from app.middleware.auth import get_tenant_id_from_api_key


async def get_current_tenant(
    x_api_key: Optional[str] = Header(None, alias="X-API-KEY"),
) -> UUID:
    if x_api_key is None:
        raise AuthenticationError(
            error_code="MISSING_API_KEY",
            message="X-API-KEY header is required",
        )

    tenant_id = get_tenant_id_from_api_key(x_api_key)
    if tenant_id is None:
        raise AuthenticationError(
            error_code="INVALID_API_KEY",
            message="Invalid API key",
        )

    return tenant_id
