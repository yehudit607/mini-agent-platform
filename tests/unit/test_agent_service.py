"""Unit tests for AgentService."""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.exc import IntegrityError

from app.exceptions import DuplicateError, NotFoundError, ForbiddenError
from app.services.agent_service import AgentService
from app.schemas.agent import AgentCreate, AgentUpdate


class TestAgentService:
    """Tests for AgentService business logic."""

    @pytest.fixture
    def mock_session(self):
        """Create mock database session."""
        return MagicMock()

    @pytest.fixture
    def mock_agent_repository(self):
        """Create mock AgentRepository."""
        repo = MagicMock()
        repo.get_by_name = AsyncMock(return_value=None)
        repo.get_by_id = AsyncMock()
        repo.list_all = AsyncMock(return_value=[])
        repo.list_by_tool_name = AsyncMock(return_value=[])
        repo.create = AsyncMock()
        repo.update = AsyncMock()
        repo.delete = AsyncMock(return_value=True)
        return repo

    @pytest.fixture
    def mock_tool_repository(self):
        """Create mock ToolRepository."""
        repo = MagicMock()
        repo.get_by_id = AsyncMock()
        return repo

    def create_mock_agent(self, agent_id=None, name="Test Agent", tools=None):
        """Helper to create a mock agent."""
        agent = MagicMock()
        agent.id = agent_id or uuid4()
        agent.name = name
        agent.role = "assistant"
        agent.description = "Test description"
        agent.tool_links = []

        if tools:
            for tool in tools:
                link = MagicMock()
                link.tool = tool
                agent.tool_links.append(link)

        return agent

    def create_mock_tool(self, tool_id=None, name="test_tool"):
        """Helper to create a mock tool."""
        tool = MagicMock()
        tool.id = tool_id or uuid4()
        tool.name = name
        tool.description = "Test tool"
        return tool

    @pytest.mark.asyncio
    async def test_create_agent_success(
        self, mock_session, mock_agent_repository, mock_tool_repository
    ):
        """create_agent creates agent with valid data."""
        tenant_id = uuid4()
        tool_id = uuid4()
        tool = self.create_mock_tool(tool_id=tool_id)
        agent = self.create_mock_agent(tools=[tool])

        mock_tool_repository.get_by_id.return_value = tool
        mock_agent_repository.create.return_value = agent

        service = AgentService(mock_session)
        service.repository = mock_agent_repository
        service.tool_repository = mock_tool_repository

        data = AgentCreate(
            name="New Agent",
            role="assistant",
            description="Test",
            tool_ids=[tool_id],
        )

        result = await service.create_agent(tenant_id, data)

        assert result == agent
        mock_agent_repository.get_by_name.assert_called_once_with(tenant_id, "New Agent")
        mock_tool_repository.get_by_id.assert_called_once_with(tenant_id, tool_id)
        mock_agent_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_agent_duplicate_name(
        self, mock_session, mock_agent_repository, mock_tool_repository
    ):
        """create_agent raises DuplicateError for existing name."""
        tenant_id = uuid4()
        existing_agent = self.create_mock_agent(name="Existing Agent")
        mock_agent_repository.get_by_name.return_value = existing_agent

        service = AgentService(mock_session)
        service.repository = mock_agent_repository
        service.tool_repository = mock_tool_repository

        data = AgentCreate(
            name="Existing Agent",
            role="assistant",
            description="Test",
            tool_ids=[],
        )

        with pytest.raises(DuplicateError) as exc_info:
            await service.create_agent(tenant_id, data)

        assert exc_info.value.error_code == "DUPLICATE_AGENT_NAME"
        assert "already exists" in exc_info.value.message
        mock_agent_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_agent_cross_tenant_tool(
        self, mock_session, mock_agent_repository, mock_tool_repository
    ):
        """create_agent raises ForbiddenError for tool from another tenant."""
        tenant_id = uuid4()
        tool_id = uuid4()

        # Tool not found (belongs to another tenant)
        mock_tool_repository.get_by_id.return_value = None

        service = AgentService(mock_session)
        service.repository = mock_agent_repository
        service.tool_repository = mock_tool_repository

        data = AgentCreate(
            name="Agent",
            role="assistant",
            description="Test",
            tool_ids=[tool_id],
        )

        with pytest.raises(ForbiddenError) as exc_info:
            await service.create_agent(tenant_id, data)

        assert exc_info.value.error_code == "CROSS_TENANT_TOOL"
        assert "another tenant" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_create_agent_validates_all_tools(
        self, mock_session, mock_agent_repository, mock_tool_repository
    ):
        """create_agent validates all tools before creation."""
        tenant_id = uuid4()
        tool1_id = uuid4()
        tool2_id = uuid4()
        tool3_id = uuid4()

        tool1 = self.create_mock_tool(tool_id=tool1_id)
        tool2 = self.create_mock_tool(tool_id=tool2_id)

        async def mock_get_tool(tid, tool_id):
            if tool_id == tool1_id:
                return tool1
            elif tool_id == tool2_id:
                return tool2
            else:
                return None  # tool3 doesn't exist

        mock_tool_repository.get_by_id.side_effect = mock_get_tool

        service = AgentService(mock_session)
        service.repository = mock_agent_repository
        service.tool_repository = mock_tool_repository

        data = AgentCreate(
            name="Agent",
            role="assistant",
            description="Test",
            tool_ids=[tool1_id, tool2_id, tool3_id],
        )

        with pytest.raises(ForbiddenError):
            await service.create_agent(tenant_id, data)

    @pytest.mark.asyncio
    async def test_get_agent_success(self, mock_session, mock_agent_repository):
        """get_agent returns agent by ID."""
        tenant_id = uuid4()
        agent_id = uuid4()
        agent = self.create_mock_agent(agent_id=agent_id)

        mock_agent_repository.get_by_id.return_value = agent

        service = AgentService(mock_session)
        service.repository = mock_agent_repository

        result = await service.get_agent(tenant_id, agent_id)

        assert result == agent
        mock_agent_repository.get_by_id.assert_called_once_with(tenant_id, agent_id)

    @pytest.mark.asyncio
    async def test_get_agent_not_found(self, mock_session, mock_agent_repository):
        """get_agent raises NotFoundError when agent doesn't exist."""
        tenant_id = uuid4()
        agent_id = uuid4()

        mock_agent_repository.get_by_id.return_value = None

        service = AgentService(mock_session)
        service.repository = mock_agent_repository

        with pytest.raises(NotFoundError) as exc_info:
            await service.get_agent(tenant_id, agent_id)

        assert exc_info.value.error_code == "AGENT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_agent_for_execution_returns_403(
        self, mock_session, mock_agent_repository
    ):
        """get_agent_for_execution returns ForbiddenError instead of NotFoundError."""
        tenant_id = uuid4()
        agent_id = uuid4()

        mock_agent_repository.get_by_id.return_value = None

        service = AgentService(mock_session)
        service.repository = mock_agent_repository

        with pytest.raises(ForbiddenError) as exc_info:
            await service.get_agent_for_execution(tenant_id, agent_id)

        assert exc_info.value.error_code == "TENANT_ISOLATION_VIOLATION"
        assert "another tenant" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_list_agents_all(self, mock_session, mock_agent_repository):
        """list_agents returns all agents when no filter."""
        tenant_id = uuid4()
        agents = [self.create_mock_agent() for _ in range(3)]
        mock_agent_repository.list_all.return_value = agents

        service = AgentService(mock_session)
        service.repository = mock_agent_repository

        result = await service.list_agents(tenant_id)

        assert len(result) == 3
        mock_agent_repository.list_all.assert_called_once_with(tenant_id)

    @pytest.mark.asyncio
    async def test_list_agents_by_tool_name(
        self, mock_session, mock_agent_repository
    ):
        """list_agents filters by tool name."""
        tenant_id = uuid4()
        agents = [self.create_mock_agent()]
        mock_agent_repository.list_by_tool_name.return_value = agents

        service = AgentService(mock_session)
        service.repository = mock_agent_repository

        result = await service.list_agents(tenant_id, tool_name="search")

        assert len(result) == 1
        mock_agent_repository.list_by_tool_name.assert_called_once_with(
            tenant_id, "search"
        )

    @pytest.mark.asyncio
    async def test_update_agent_success(
        self, mock_session, mock_agent_repository, mock_tool_repository
    ):
        """update_agent updates agent fields."""
        tenant_id = uuid4()
        agent_id = uuid4()
        existing_agent = self.create_mock_agent(agent_id=agent_id, name="Old Name")
        updated_agent = self.create_mock_agent(agent_id=agent_id, name="New Name")

        mock_agent_repository.get_by_id.return_value = existing_agent
        mock_agent_repository.update.return_value = updated_agent

        service = AgentService(mock_session)
        service.repository = mock_agent_repository
        service.tool_repository = mock_tool_repository

        data = AgentUpdate(name="New Name", role="worker")
        result = await service.update_agent(tenant_id, agent_id, data)

        assert result == updated_agent
        mock_agent_repository.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_agent_duplicate_name(
        self, mock_session, mock_agent_repository, mock_tool_repository
    ):
        """update_agent raises DuplicateError for conflicting name."""
        tenant_id = uuid4()
        agent_id = uuid4()
        other_agent_id = uuid4()

        existing_agent = self.create_mock_agent(agent_id=agent_id, name="Agent1")
        other_agent = self.create_mock_agent(agent_id=other_agent_id, name="Agent2")

        async def mock_get_by_id(tid, aid):
            if aid == agent_id:
                return existing_agent
            return None

        mock_agent_repository.get_by_id.side_effect = mock_get_by_id
        mock_agent_repository.get_by_name.return_value = other_agent

        service = AgentService(mock_session)
        service.repository = mock_agent_repository
        service.tool_repository = mock_tool_repository

        data = AgentUpdate(name="Agent2")  # Conflicts with other_agent

        with pytest.raises(DuplicateError) as exc_info:
            await service.update_agent(tenant_id, agent_id, data)

        assert exc_info.value.error_code == "DUPLICATE_AGENT_NAME"

    @pytest.mark.asyncio
    async def test_update_agent_validates_tools(
        self, mock_session, mock_agent_repository, mock_tool_repository
    ):
        """update_agent validates new tools."""
        tenant_id = uuid4()
        agent_id = uuid4()
        tool_id = uuid4()

        existing_agent = self.create_mock_agent(agent_id=agent_id)
        mock_agent_repository.get_by_id.return_value = existing_agent
        mock_tool_repository.get_by_id.return_value = None  # Tool doesn't exist

        service = AgentService(mock_session)
        service.repository = mock_agent_repository
        service.tool_repository = mock_tool_repository

        data = AgentUpdate(tool_ids=[tool_id])

        with pytest.raises(ForbiddenError) as exc_info:
            await service.update_agent(tenant_id, agent_id, data)

        assert exc_info.value.error_code == "CROSS_TENANT_TOOL"

    @pytest.mark.asyncio
    async def test_delete_agent_success(self, mock_session, mock_agent_repository):
        """delete_agent removes agent."""
        tenant_id = uuid4()
        agent_id = uuid4()
        agent = self.create_mock_agent(agent_id=agent_id)

        mock_agent_repository.get_by_id.return_value = agent
        mock_agent_repository.delete.return_value = True

        service = AgentService(mock_session)
        service.repository = mock_agent_repository

        await service.delete_agent(tenant_id, agent_id)

        mock_agent_repository.delete.assert_called_once_with(tenant_id, agent_id)

    @pytest.mark.asyncio
    async def test_delete_agent_not_found(self, mock_session, mock_agent_repository):
        """delete_agent raises NotFoundError when agent doesn't exist."""
        tenant_id = uuid4()
        agent_id = uuid4()

        mock_agent_repository.get_by_id.return_value = None

        service = AgentService(mock_session)
        service.repository = mock_agent_repository

        with pytest.raises(NotFoundError):
            await service.delete_agent(tenant_id, agent_id)

    @pytest.mark.asyncio
    async def test_delete_agent_repository_fails(
        self, mock_session, mock_agent_repository
    ):
        """delete_agent raises NotFoundError when repository delete fails."""
        tenant_id = uuid4()
        agent_id = uuid4()
        agent = self.create_mock_agent(agent_id=agent_id)

        mock_agent_repository.get_by_id.return_value = agent
        mock_agent_repository.delete.return_value = False

        service = AgentService(mock_session)
        service.repository = mock_agent_repository

        with pytest.raises(NotFoundError):
            await service.delete_agent(tenant_id, agent_id)
