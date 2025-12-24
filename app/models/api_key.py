import hashlib
import secrets
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.tenant import Tenant


class APIKey(SQLModel, table=True):
    __tablename__ = "api_keys"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    tenant_id: UUID = Field(foreign_key="tenants.id", index=True)
    key_hash: str = Field(max_length=64)
    key_prefix: str = Field(max_length=12)
    name: str = Field(max_length=100)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = Field(default=None)

    tenant: Optional["Tenant"] = Relationship(back_populates="api_keys")

    @staticmethod
    def hash_key(plain_key: str) -> str:
        return hashlib.sha256(plain_key.encode()).hexdigest()

    @staticmethod
    def generate_key() -> tuple[str, str, str]:
        """
        Generate a new API key.
        Returns: (plain_key, key_hash, key_prefix)
        """
        random_part = secrets.token_hex(16)
        plain_key = f"map_{random_part}"
        key_hash = APIKey.hash_key(plain_key)
        key_prefix = plain_key[:12]
        return plain_key, key_hash, key_prefix
