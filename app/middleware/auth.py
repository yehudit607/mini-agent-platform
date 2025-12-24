from uuid import UUID

# In production, replace with database lookup and hashed keys
TENANT_REGISTRY: dict[str, UUID] = {
    "tenant-a-test-key": UUID("11111111-1111-1111-1111-111111111111"),
    "tenant-b-test-key": UUID("22222222-2222-2222-2222-222222222222"),
    "tenant-a-key": UUID("11111111-1111-1111-1111-111111111111"),
    "tenant-b-key": UUID("22222222-2222-2222-2222-222222222222"),
}


def get_tenant_id_from_api_key(api_key: str) -> UUID | None:
    return TENANT_REGISTRY.get(api_key)
