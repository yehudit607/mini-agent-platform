"""Unit tests for ToolService."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import IntegrityError

from app.exceptions import DuplicateError, NotFoundError, ForbiddenError, DependencyError
from app.services.tool_service import ToolService
from app.schemas.tool import ToolCreate, ToolUpdate


class TestToolService:
    """Tests for ToolService business logic."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def mock_tool_repository(self):
        """Create mock ToolRepository."""
        repo = MagicMock()
        repo.get_by_name = AsyncMock(return_value=None)
        repo.get_by_id = AsyncMock()
        repo.list_all = AsyncMock(return_value=[])
        repo.list_by_agent_name = AsyncMock(return_value=[])
        repo.create = AsyncMock()
        repo.update = AsyncMock()
        repo.delete = AsyncMock(return_value=True)
        repo.get_dependent_agents = AsyncMock(return_value=[])
        return repo

    def create_mock_tool(self, tool_id=None, name="test_tool"):
        """Helper to create a mock tool."""
        tool = MagicMock()
        tool.id = tool_id or uuid4()
        tool.name = name
        tool.description = "Test tool description"
        return tool

    @pytest.mark.asyncio
    async def test_create_tool_success(self, mock_session, mock_tool_repository):
        """create_tool creates tool with valid data."""
        tenant_id = uuid4()
        tool = self.create_mock_tool()

        mock_tool_repository.create.return_value = tool

        service = ToolService(mock_session)
        service.repository = mock_tool_repository

        data = ToolCreate(name="new_tool", description="A new tool")
        result = await service.create_tool(tenant_id, data)

        assert result == tool
        mock_tool_repository.get_by_name.assert_called_once_with(tenant_id, "new_tool")
        mock_tool_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_tool_duplicate_name(self, mock_session, mock_tool_repository):
        """create_tool raises DuplicateError for existing name."""
        tenant_id = uuid4()
        existing_tool = self.create_mock_tool(name="existing_tool")
        mock_tool_repository.get_by_name.return_value = existing_tool

        service = ToolService(mock_session)
        service.repository = mock_tool_repository

        data = ToolCreate(name="existing_tool", description="Test")

        with pytest.raises(DuplicateError) as exc_info:
            await service.create_tool(tenant_id, data)

        assert exc_info.value.error_code == "DUPLICATE_TOOL_NAME"
        assert "already exists" in exc_info.value.message
        mock_tool_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_tool_integrity_error(self, mock_session, mock_tool_repository):
        """create_tool handles IntegrityError from database."""
        tenant_id = uuid4()
        mock_tool_repository.create.side_effect = IntegrityError(None, None, None)

        service = ToolService(mock_session)
        service.repository = mock_tool_repository

        data = ToolCreate(name="tool", description="Test")

        with pytest.raises(DuplicateError) as exc_info:
            await service.create_tool(tenant_id, data)

        assert exc_info.value.error_code == "DUPLICATE_TOOL_NAME"

    @pytest.mark.asyncio
    async def test_get_tool_success(self, mock_session, mock_tool_repository):
        """get_tool returns tool by ID."""
        tenant_id = uuid4()
        tool_id = uuid4()
        tool = self.create_mock_tool(tool_id=tool_id)

        mock_tool_repository.get_by_id.return_value = tool

        service = ToolService(mock_session)
        service.repository = mock_tool_repository

        result = await service.get_tool(tenant_id, tool_id)

        assert result == tool
        mock_tool_repository.get_by_id.assert_called_once_with(tenant_id, tool_id)

    @pytest.mark.asyncio
    async def test_get_tool_not_found(self, mock_session, mock_tool_repository):
        """get_tool raises NotFoundError when tool doesn't exist."""
        tenant_id = uuid4()
        tool_id = uuid4()

        mock_tool_repository.get_by_id.return_value = None

        service = ToolService(mock_session)
        service.repository = mock_tool_repository

        with pytest.raises(NotFoundError) as exc_info:
            await service.get_tool(tenant_id, tool_id)

        assert exc_info.value.error_code == "TOOL_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_tool_or_forbidden_returns_403(
        self, mock_session, mock_tool_repository
    ):
        """get_tool_or_forbidden returns ForbiddenError for security."""
        tenant_id = uuid4()
        tool_id = uuid4()

        mock_tool_repository.get_by_id.return_value = None

        service = ToolService(mock_session)
        service.repository = mock_tool_repository

        with pytest.raises(ForbiddenError) as exc_info:
            await service.get_tool_or_forbidden(tenant_id, tool_id, check_exists=True)

        assert exc_info.value.error_code == "TENANT_ISOLATION_VIOLATION"
        assert "another tenant" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_get_tool_or_forbidden_returns_404_when_not_checking(
        self, mock_session, mock_tool_repository
    ):
        """get_tool_or_forbidden returns NotFoundError when check_exists=False."""
        tenant_id = uuid4()
        tool_id = uuid4()

        mock_tool_repository.get_by_id.return_value = None

        service = ToolService(mock_session)
        service.repository = mock_tool_repository

        with pytest.raises(NotFoundError) as exc_info:
            await service.get_tool_or_forbidden(tenant_id, tool_id, check_exists=False)

        assert exc_info.value.error_code == "TOOL_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_list_tools_all(self, mock_session, mock_tool_repository):
        """list_tools returns all tools when no filter."""
        tenant_id = uuid4()
        tools = [self.create_mock_tool() for _ in range(3)]
        mock_tool_repository.list_all.return_value = tools

        service = ToolService(mock_session)
        service.repository = mock_tool_repository

        result = await service.list_tools(tenant_id)

        assert len(result) == 3
        mock_tool_repository.list_all.assert_called_once_with(tenant_id)

    @pytest.mark.asyncio
    async def test_list_tools_by_agent_name(self, mock_session, mock_tool_repository):
        """list_tools filters by agent name."""
        tenant_id = uuid4()
        tools = [self.create_mock_tool()]
        mock_tool_repository.list_by_agent_name.return_value = tools

        service = ToolService(mock_session)
        service.repository = mock_tool_repository

        result = await service.list_tools(tenant_id, agent_name="MyAgent")

        assert len(result) == 1
        mock_tool_repository.list_by_agent_name.assert_called_once_with(
            tenant_id, "MyAgent"
        )

    @pytest.mark.asyncio
    async def test_update_tool_success(self, mock_session, mock_tool_repository):
        """update_tool updates tool fields."""
        tenant_id = uuid4()
        tool_id = uuid4()
        existing_tool = self.create_mock_tool(tool_id=tool_id, name="old_name")
        updated_tool = self.create_mock_tool(tool_id=tool_id, name="new_name")

        mock_tool_repository.get_by_id.return_value = existing_tool
        mock_tool_repository.update.return_value = updated_tool

        service = ToolService(mock_session)
        service.repository = mock_tool_repository

        data = ToolUpdate(name="new_name", description="Updated description")
        result = await service.update_tool(tenant_id, tool_id, data)

        assert result == updated_tool
        mock_tool_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_tool_duplicate_name(self, mock_session, mock_tool_repository):
        """update_tool raises DuplicateError for conflicting name."""
        tenant_id = uuid4()
        tool_id = uuid4()
        other_tool_id = uuid4()

        existing_tool = self.create_mock_tool(tool_id=tool_id, name="tool1")
        other_tool = self.create_mock_tool(tool_id=other_tool_id, name="tool2")

        mock_tool_repository.get_by_id.return_value = existing_tool
        mock_tool_repository.get_by_name.return_value = other_tool

        service = ToolService(mock_session)
        service.repository = mock_tool_repository

        data = ToolUpdate(name="tool2")  # Conflicts with other_tool

        with pytest.raises(DuplicateError) as exc_info:
            await service.update_tool(tenant_id, tool_id, data)

        assert exc_info.value.error_code == "DUPLICATE_TOOL_NAME"

    @pytest.mark.asyncio
    async def test_update_tool_same_name_allowed(
        self, mock_session, mock_tool_repository
    ):
        """update_tool allows updating to same name."""
        tenant_id = uuid4()
        tool_id = uuid4()
        existing_tool = self.create_mock_tool(tool_id=tool_id, name="same_name")
        updated_tool = self.create_mock_tool(tool_id=tool_id, name="same_name")

        mock_tool_repository.get_by_id.return_value = existing_tool
        mock_tool_repository.get_by_name.return_value = existing_tool
        mock_tool_repository.update.return_value = updated_tool

        service = ToolService(mock_session)
        service.repository = mock_tool_repository

        data = ToolUpdate(name="same_name", description="New description")
        result = await service.update_tool(tenant_id, tool_id, data)

        assert result == updated_tool

    @pytest.mark.asyncio
    async def test_delete_tool_success(self, mock_session, mock_tool_repository):
        """delete_tool removes tool."""
        tenant_id = uuid4()
        tool_id = uuid4()
        tool = self.create_mock_tool(tool_id=tool_id)

        mock_tool_repository.get_by_id.return_value = tool
        mock_tool_repository.get_dependent_agents.return_value = []
        mock_tool_repository.delete.return_value = True

        service = ToolService(mock_session)
        service.repository = mock_tool_repository

        await service.delete_tool(tenant_id, tool_id)

        mock_tool_repository.delete.assert_called_once_with(tenant_id, tool_id)

    @pytest.mark.asyncio
    async def test_delete_tool_with_dependencies(
        self, mock_session, mock_tool_repository
    ):
        """delete_tool raises DependencyError when tool is in use."""
        tenant_id = uuid4()
        tool_id = uuid4()
        tool = self.create_mock_tool(tool_id=tool_id)

        mock_tool_repository.get_by_id.return_value = tool
        mock_tool_repository.get_dependent_agents.return_value = [
            "Agent1",
            "Agent2",
        ]

        service = ToolService(mock_session)
        service.repository = mock_tool_repository

        with pytest.raises(DependencyError) as exc_info:
            await service.delete_tool(tenant_id, tool_id)

        assert exc_info.value.error_code == "TOOL_IN_USE"
        assert "associated with agents" in exc_info.value.message
        assert exc_info.value.details["dependent_agents"] == ["Agent1", "Agent2"]
        mock_tool_repository.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_tool_not_found(self, mock_session, mock_tool_repository):
        """delete_tool raises NotFoundError when tool doesn't exist."""
        tenant_id = uuid4()
        tool_id = uuid4()

        mock_tool_repository.get_by_id.return_value = None

        service = ToolService(mock_session)
        service.repository = mock_tool_repository

        with pytest.raises(NotFoundError):
            await service.delete_tool(tenant_id, tool_id)

    @pytest.mark.asyncio
    async def test_delete_tool_repository_fails(
        self, mock_session, mock_tool_repository
    ):
        """delete_tool raises NotFoundError when repository delete fails."""
        tenant_id = uuid4()
        tool_id = uuid4()
        tool = self.create_mock_tool(tool_id=tool_id)

        mock_tool_repository.get_by_id.return_value = tool
        mock_tool_repository.get_dependent_agents.return_value = []
        mock_tool_repository.delete.return_value = False

        service = ToolService(mock_session)
        service.repository = mock_tool_repository

        with pytest.raises(NotFoundError):
            await service.delete_tool(tenant_id, tool_id)
