"""Add tenants and api_keys tables.

Revision ID: 002_api_keys
Revises: 001_initial
Create Date: 2025-12-24

"""
import hashlib
from datetime import datetime, timezone
from typing import Sequence, Union
from uuid import UUID

from alembic import op
import sqlalchemy as sa

revision: str = "002_api_keys"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TENANT_A_ID = "11111111-1111-1111-1111-111111111111"
TENANT_B_ID = "22222222-2222-2222-2222-222222222222"


def hash_key(plain_key: str) -> str:
    return hashlib.sha256(plain_key.encode()).hexdigest()


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "api_keys",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("key_prefix", sa.String(length=12), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_api_keys_tenant_id", "api_keys", ["tenant_id"])
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"], unique=True)

    # Seed demo tenants
    tenants_table = sa.table(
        "tenants",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("is_active", sa.Boolean()),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
    )

    now = utcnow()
    op.bulk_insert(
        tenants_table,
        [
            {
                "id": TENANT_A_ID,
                "name": "Demo Tenant A",
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
            {
                "id": TENANT_B_ID,
                "name": "Demo Tenant B",
                "is_active": True,
                "created_at": now,
                "updated_at": now,
            },
        ],
    )

    # Seed demo API keys
    api_keys_table = sa.table(
        "api_keys",
        sa.column("id", sa.Uuid()),
        sa.column("tenant_id", sa.Uuid()),
        sa.column("key_hash", sa.String()),
        sa.column("key_prefix", sa.String()),
        sa.column("name", sa.String()),
        sa.column("is_active", sa.Boolean()),
        sa.column("created_at", sa.DateTime()),
        sa.column("last_used_at", sa.DateTime()),
    )

    op.bulk_insert(
        api_keys_table,
        [
            {
                "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                "tenant_id": TENANT_A_ID,
                "key_hash": hash_key("tenant-a-key"),
                "key_prefix": "tenant-a-ke",
                "name": "Demo Key A",
                "is_active": True,
                "created_at": now,
                "last_used_at": None,
            },
            {
                "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaab",
                "tenant_id": TENANT_A_ID,
                "key_hash": hash_key("tenant-a-test-key"),
                "key_prefix": "tenant-a-te",
                "name": "Test Key A",
                "is_active": True,
                "created_at": now,
                "last_used_at": None,
            },
            {
                "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                "tenant_id": TENANT_B_ID,
                "key_hash": hash_key("tenant-b-key"),
                "key_prefix": "tenant-b-ke",
                "name": "Demo Key B",
                "is_active": True,
                "created_at": now,
                "last_used_at": None,
            },
            {
                "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbc",
                "tenant_id": TENANT_B_ID,
                "key_hash": hash_key("tenant-b-test-key"),
                "key_prefix": "tenant-b-te",
                "name": "Test Key B",
                "is_active": True,
                "created_at": now,
                "last_used_at": None,
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("api_keys")
    op.drop_table("tenants")
