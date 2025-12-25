"""Unit tests for AuthService."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.exceptions import AuthenticationError
from app.services.auth_service import AuthService
from app.models.api_key import APIKey


class TestAuthService:
    """Tests for AuthService authentication logic."""

    @pytest.fixture
    def mock_repository(self):
        """Create a mock APIKeyRepository."""
        repo = MagicMock()
        repo.get_by_hash = AsyncMock()
        repo.update_last_used = AsyncMock()
        return repo

    @pytest.fixture
    def mock_session(self):
        """Create a mock AsyncSession."""
        return MagicMock()

    def create_mock_api_key(self, tenant_id=None, is_active=True, tenant_active=True):
        """Helper to create a mock APIKey."""
        api_key = MagicMock(spec=APIKey)
        api_key.id = uuid4()
        api_key.tenant_id = tenant_id or uuid4()
        api_key.key_prefix = "sk_test_abc"
        api_key.is_active = is_active
        api_key.created_at = datetime.now(timezone.utc)

        # Mock tenant
        tenant = MagicMock()
        tenant.id = api_key.tenant_id
        tenant.is_active = tenant_active
        api_key.tenant = tenant

        return api_key

    @pytest.mark.asyncio
    async def test_validate_api_key_success(self, mock_session, mock_repository):
        """validate_api_key returns tenant_id for valid key."""
        tenant_id = uuid4()
        api_key = self.create_mock_api_key(tenant_id=tenant_id)
        mock_repository.get_by_hash.return_value = api_key

        service = AuthService(mock_session)
        service.repository = mock_repository

        result = await service.validate_api_key("sk_test_validkey123")

        assert result == tenant_id
        mock_repository.get_by_hash.assert_called_once()
        mock_repository.update_last_used.assert_called_once_with(api_key.id)

    @pytest.mark.asyncio
    async def test_validate_api_key_hashes_input(self, mock_session, mock_repository):
        """validate_api_key hashes the plain key before lookup."""
        api_key = self.create_mock_api_key()
        mock_repository.get_by_hash.return_value = api_key

        service = AuthService(mock_session)
        service.repository = mock_repository

        plain_key = "sk_test_plainkey456"
        await service.validate_api_key(plain_key)

        # Verify it called get_by_hash with hashed key
        called_hash = mock_repository.get_by_hash.call_args[0][0]
        assert called_hash != plain_key  # Should be hashed
        assert len(called_hash) == 64  # SHA-256 hex length

    @pytest.mark.asyncio
    async def test_validate_api_key_not_found(self, mock_session, mock_repository):
        """validate_api_key raises AuthenticationError when key not found."""
        mock_repository.get_by_hash.return_value = None

        service = AuthService(mock_session)
        service.repository = mock_repository

        with pytest.raises(AuthenticationError) as exc_info:
            await service.validate_api_key("sk_test_invalidkey")

        assert exc_info.value.error_code == "INVALID_API_KEY"
        assert "Invalid API key" in exc_info.value.message
        mock_repository.update_last_used.assert_not_called()

    @pytest.mark.asyncio
    async def test_validate_api_key_inactive(self, mock_session, mock_repository):
        """validate_api_key raises AuthenticationError for inactive key."""
        api_key = self.create_mock_api_key(is_active=False)
        mock_repository.get_by_hash.return_value = api_key

        service = AuthService(mock_session)
        service.repository = mock_repository

        with pytest.raises(AuthenticationError) as exc_info:
            await service.validate_api_key("sk_test_inactivekey")

        assert exc_info.value.error_code == "API_KEY_INACTIVE"
        assert "deactivated" in exc_info.value.message
        mock_repository.update_last_used.assert_not_called()

    @pytest.mark.asyncio
    async def test_validate_api_key_inactive_tenant(self, mock_session, mock_repository):
        """validate_api_key raises AuthenticationError for inactive tenant."""
        api_key = self.create_mock_api_key(tenant_active=False)
        mock_repository.get_by_hash.return_value = api_key

        service = AuthService(mock_session)
        service.repository = mock_repository

        with pytest.raises(AuthenticationError) as exc_info:
            await service.validate_api_key("sk_test_key")

        assert exc_info.value.error_code == "TENANT_INACTIVE"
        assert "Tenant account" in exc_info.value.message
        mock_repository.update_last_used.assert_not_called()

    @pytest.mark.asyncio
    async def test_validate_api_key_updates_last_used(self, mock_session, mock_repository):
        """validate_api_key updates last_used timestamp."""
        api_key = self.create_mock_api_key()
        mock_repository.get_by_hash.return_value = api_key

        service = AuthService(mock_session)
        service.repository = mock_repository

        await service.validate_api_key("sk_test_key")

        mock_repository.update_last_used.assert_called_once_with(api_key.id)

    @pytest.mark.asyncio
    async def test_validate_api_key_all_checks_pass(self, mock_session, mock_repository):
        """validate_api_key performs all security checks in order."""
        api_key = self.create_mock_api_key()
        mock_repository.get_by_hash.return_value = api_key

        service = AuthService(mock_session)
        service.repository = mock_repository

        # Should not raise
        tenant_id = await service.validate_api_key("sk_test_validkey")

        assert tenant_id == api_key.tenant_id

    @pytest.mark.asyncio
    async def test_different_keys_hash_differently(self, mock_session, mock_repository):
        """Different API keys produce different hashes."""
        api_key1 = self.create_mock_api_key()
        api_key2 = self.create_mock_api_key()
        mock_repository.get_by_hash.return_value = api_key1

        service = AuthService(mock_session)
        service.repository = mock_repository

        await service.validate_api_key("sk_test_key1")
        hash1 = mock_repository.get_by_hash.call_args[0][0]

        await service.validate_api_key("sk_test_key2")
        hash2 = mock_repository.get_by_hash.call_args[0][0]

        assert hash1 != hash2
