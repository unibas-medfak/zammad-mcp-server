"""Tests for Zammad MCP Server tools and server functionality."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest


class TestTicketTools:
    """Test suite for ticket-related tools."""

    def test_get_ticket_success(self, unrestricted_controller: Any) -> None:
        """Test getting a ticket successfully."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            mock_ticket = MagicMock()
            mock_ticket.model_dump.return_value = {
                "id": 1,
                "title": "Test Ticket",
                "group": "Support",
            }
            mock_client.get_ticket.return_value = mock_ticket
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = unrestricted_controller

            from zammad_mcp_server.server import get_ticket
            result = get_ticket(1)

            assert result["id"] == 1
            assert result["title"] == "Test Ticket"

    def test_get_ticket_not_found(self, unrestricted_controller: Any) -> None:
        """Test getting a non-existent ticket."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            from zammad_mcp_server.client import NotFoundError
            mock_client.get_ticket.side_effect = NotFoundError("Not found", 404)
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = unrestricted_controller

            from zammad_mcp_server.server import get_ticket
            result = get_ticket(999)

            assert "error" in result
            assert "999" in result["error"]

    def test_get_ticket_access_denied(self, restricted_controller: Any) -> None:
        """Test getting a ticket with restricted access."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            mock_ticket = MagicMock()
            mock_ticket.model_dump.return_value = {
                "id": 1,
                "title": "Test",
                "group": {"name": "Admin"},  # Restricted group
            }
            mock_client.get_ticket.return_value = mock_ticket
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = restricted_controller

            from zammad_mcp_server.server import get_ticket
            with pytest.raises(PermissionError, match="Access denied"):
                get_ticket(1)

    def test_search_tickets(self, unrestricted_controller: Any) -> None:
        """Test searching tickets."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            mock_result = MagicMock()
            mock_result.items = [
                MagicMock(model_dump=lambda: {"id": 1, "title": "Ticket 1"}),
                MagicMock(model_dump=lambda: {"id": 2, "title": "Ticket 2"}),
            ]
            mock_result.total_count = 2
            mock_client.search_tickets.return_value = mock_result
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = unrestricted_controller

            from zammad_mcp_server.server import search_tickets
            result = search_tickets(query="test")

            assert len(result["tickets"]) == 2
            assert result["total_count"] == 2

    def test_create_ticket(self, unrestricted_controller: Any) -> None:
        """Test creating a ticket."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            mock_ticket = MagicMock()
            mock_ticket.model_dump.return_value = {
                "id": 999,
                "title": "New Ticket",
                "group": "Support",
            }
            mock_client.create_ticket.return_value = mock_ticket
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = unrestricted_controller

            from zammad_mcp_server.server import create_ticket
            result = create_ticket(
                title="New Ticket",
                group="Support",
                customer="test@example.com",
            )

            assert result["id"] == 999
            assert result["title"] == "New Ticket"

    def test_create_ticket_access_denied(self, read_only_controller: Any) -> None:
        """Test creating a ticket with read-only access."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_get_client.return_value = MagicMock()
            mock_get_controller.return_value = read_only_controller

            from zammad_mcp_server.server import create_ticket
            with pytest.raises(PermissionError):
                create_ticket(title="New", group="Support")

    def test_update_ticket(self, unrestricted_controller: Any) -> None:
        """Test updating a ticket."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            mock_ticket = MagicMock()
            mock_ticket.model_dump.return_value = {
                "id": 1,
                "title": "Updated Title",
            }
            mock_client.update_ticket.return_value = mock_ticket
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = unrestricted_controller

            from zammad_mcp_server.server import update_ticket
            result = update_ticket(ticket_id=1, title="Updated Title")

            assert result["title"] == "Updated Title"

    def test_delete_ticket(self, unrestricted_controller: Any) -> None:
        """Test deleting a ticket."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            mock_client.delete_ticket.return_value = True
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = unrestricted_controller

            from zammad_mcp_server.server import delete_ticket
            result = delete_ticket(1)

            assert result["success"] is True

    def test_delete_ticket_access_denied(self, restricted_controller: Any) -> None:
        """Test deleting a ticket with restricted access."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_get_client.return_value = MagicMock()
            mock_get_controller.return_value = restricted_controller

            from zammad_mcp_server.server import delete_ticket
            with pytest.raises(PermissionError):
                delete_ticket(1)

    def test_get_ticket_articles(self, unrestricted_controller: Any) -> None:
        """Test getting ticket articles."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            mock_article = MagicMock()
            mock_article.model_dump.return_value = {"id": 1, "body": "Test"}
            mock_client.get_ticket_articles.return_value = [mock_article]
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = unrestricted_controller

            from zammad_mcp_server.server import get_ticket_articles
            result = get_ticket_articles(1)

            assert result["ticket_id"] == 1
            assert len(result["articles"]) == 1

    def test_create_article(self, unrestricted_controller: Any) -> None:
        """Test creating an article."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            mock_article = MagicMock()
            mock_article.model_dump.return_value = {"id": 1, "body": "New content"}
            mock_client.create_article.return_value = mock_article
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = unrestricted_controller

            from zammad_mcp_server.server import create_article
            result = create_article(ticket_id=1, body="New content")

            assert result["body"] == "New content"

    def test_set_ticket_draft(self, unrestricted_controller: Any) -> None:
        """Test proposing a reply as the ticket's shared draft."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            mock_client.get_shared_draft_id.return_value = None
            mock_client.set_shared_draft.return_value = 7
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = unrestricted_controller

            from zammad_mcp_server.server import set_ticket_draft
            result = set_ticket_draft(ticket_id=1, body="<p>Hello</p>", to="customer@example.com")

            assert result == {"ticket_id": 1, "shared_draft_id": 7}
            request = mock_client.set_shared_draft.call_args.args[0]
            assert request.type.value == "email"
            assert request.to == "customer@example.com"

    def test_set_ticket_draft_keeps_existing_draft(self, unrestricted_controller: Any) -> None:
        """Test that an existing shared draft is only replaced with overwrite."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            mock_client.get_shared_draft_id.return_value = 3
            mock_client.set_shared_draft.return_value = 3
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = unrestricted_controller

            from zammad_mcp_server.server import set_ticket_draft
            result = set_ticket_draft(ticket_id=1, body="<p>Hello</p>")

            assert "already has a shared draft" in result["error"]
            mock_client.set_shared_draft.assert_not_called()

            result = set_ticket_draft(ticket_id=1, body="<p>Hello</p>", overwrite=True)

            assert result == {"ticket_id": 1, "shared_draft_id": 3}

    def test_get_ticket_stats(self, unrestricted_controller: Any) -> None:
        """Test getting ticket statistics."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            mock_stats = MagicMock()
            mock_stats.model_dump.return_value = {
                "total": 100,
                "open": 20,
                "closed": 70,
            }
            mock_client.get_ticket_stats.return_value = mock_stats
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = unrestricted_controller

            from zammad_mcp_server.server import get_ticket_stats
            result = get_ticket_stats()

            assert result["total"] == 100
            assert result["open"] == 20

    def test_get_ticket_states(self, unrestricted_controller: Any) -> None:
        """Test getting ticket states."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            mock_client.get_ticket_states.return_value = [
                {"id": 1, "name": "new"},
                {"id": 2, "name": "open"},
            ]
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = unrestricted_controller

            from zammad_mcp_server.server import get_ticket_states
            result = get_ticket_states()

            assert len(result) == 2


class TestUserTools:
    """Test suite for user-related tools."""

    def test_get_user(self, unrestricted_controller: Any) -> None:
        """Test getting a user."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            mock_user = MagicMock()
            mock_user.model_dump.return_value = {"id": 1, "email": "test@example.com"}
            mock_client.get_user.return_value = mock_user
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = unrestricted_controller

            from zammad_mcp_server.server import get_user
            result = get_user(1)

            assert result["id"] == 1

    def test_search_users(self, unrestricted_controller: Any) -> None:
        """Test searching users."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            mock_result = MagicMock()
            mock_result.items = [
                MagicMock(model_dump=lambda: {"id": 1, "email": "user1@example.com"}),
            ]
            mock_result.total_count = 1
            mock_client.search_users.return_value = mock_result
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = unrestricted_controller

            from zammad_mcp_server.server import search_users
            result = search_users(query="test")

            assert len(result["users"]) == 1

    def test_create_user(self, unrestricted_controller: Any) -> None:
        """Test creating a user."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            mock_user = MagicMock()
            mock_user.model_dump.return_value = {"id": 1, "email": "new@example.com"}
            mock_client.create_user.return_value = mock_user
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = unrestricted_controller

            from zammad_mcp_server.server import create_user
            result = create_user(email="new@example.com", firstname="New", lastname="User")

            assert result["email"] == "new@example.com"

    def test_update_user(self, unrestricted_controller: Any) -> None:
        """Test updating a user."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            mock_user = MagicMock()
            mock_user.model_dump.return_value = {"id": 1, "firstname": "Updated"}
            mock_client.update_user.return_value = mock_user
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = unrestricted_controller

            from zammad_mcp_server.server import update_user
            result = update_user(user_id=1, firstname="Updated")

            assert result["firstname"] == "Updated"

    def test_delete_user(self, unrestricted_controller: Any) -> None:
        """Test deleting a user."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            mock_client.delete_user.return_value = True
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = unrestricted_controller

            from zammad_mcp_server.server import delete_user
            result = delete_user(1)

            assert result["success"] is True

    def test_get_current_user(self, unrestricted_controller: Any) -> None:
        """Test getting current user."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            mock_user = MagicMock()
            mock_user.model_dump.return_value = {"id": 1, "email": "me@example.com"}
            mock_client.get_current_user.return_value = mock_user
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = unrestricted_controller

            from zammad_mcp_server.server import get_current_user
            result = get_current_user()

            assert result["email"] == "me@example.com"


class TestOrganizationTools:
    """Test suite for organization-related tools."""

    def test_get_organization(self, unrestricted_controller: Any) -> None:
        """Test getting an organization."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            mock_org = MagicMock()
            mock_org.model_dump.return_value = {"id": 1, "name": "Test Org"}
            mock_client.get_organization.return_value = mock_org
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = unrestricted_controller

            from zammad_mcp_server.server import get_organization
            result = get_organization(1)

            assert result["name"] == "Test Org"

    def test_search_organizations(self, unrestricted_controller: Any) -> None:
        """Test searching organizations."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            mock_result = MagicMock()
            mock_result.items = [
                MagicMock(model_dump=lambda: {"id": 1, "name": "Org 1"}),
            ]
            mock_result.total_count = 1
            mock_client.search_organizations.return_value = mock_result
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = unrestricted_controller

            from zammad_mcp_server.server import search_organizations
            result = search_organizations(query="test")

            assert len(result["organizations"]) == 1

    def test_create_organization(self, unrestricted_controller: Any) -> None:
        """Test creating an organization."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            mock_org = MagicMock()
            mock_org.model_dump.return_value = {"id": 1, "name": "New Org"}
            mock_client.create_organization.return_value = mock_org
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = unrestricted_controller

            from zammad_mcp_server.server import create_organization
            result = create_organization(name="New Org")

            assert result["name"] == "New Org"


class TestGroupTools:
    """Test suite for group-related tools."""

    def test_get_group(self, unrestricted_controller: Any) -> None:
        """Test getting a group."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            mock_group = MagicMock()
            mock_group.model_dump.return_value = {"id": 1, "name": "Support"}
            mock_client.get_group.return_value = mock_group
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = unrestricted_controller

            from zammad_mcp_server.server import get_group
            result = get_group(1)

            assert result["name"] == "Support"

    def test_list_groups(self, unrestricted_controller: Any) -> None:
        """Test listing groups."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            mock_group = MagicMock()
            mock_group.model_dump.return_value = {"id": 1, "name": "Support"}
            mock_client.list_groups.return_value = [mock_group]
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = unrestricted_controller

            from zammad_mcp_server.server import list_groups
            result = list_groups()

            assert len(result["groups"]) == 1
            assert result["count"] == 1


class TestGroupRestrictions:
    """Test that MCP_ALLOWED_GROUPS is enforced on every ticket/group tool."""

    @pytest.fixture
    def controller(self) -> Any:
        from zammad_mcp_server.access_control import AccessController, AccessPolicy, Permission
        return AccessController(
            AccessPolicy(default_permission=Permission.ADMIN, allowed_groups={"Support"})
        )

    @pytest.fixture
    def client(self, controller: Any) -> Any:
        from zammad_mcp_server.models import Group, Ticket

        tickets = {
            1: Ticket(id=1, title="Allowed", group="Support"),
            2: Ticket(id=2, title="Forbidden", group="Admin"),
        }
        mock_client = MagicMock()
        mock_client.get_ticket.side_effect = lambda ticket_id, **_: tickets[ticket_id]
        mock_client.get_group.side_effect = lambda group_id: Group(
            id=group_id, name="Support" if group_id == 1 else "Admin"
        )
        mock_client.list_groups.return_value = [
            Group(id=1, name="Support"),
            Group(id=2, name="Admin"),
        ]
        with patch("zammad_mcp_server.server.get_client", return_value=mock_client), \
             patch("zammad_mcp_server.server.get_access_controller", return_value=controller):
            yield mock_client

    @pytest.mark.parametrize(
        ("tool", "kwargs", "client_method"),
        [
            ("get_ticket_articles", {}, "get_ticket_articles"),
            ("create_article", {"body": "hi"}, "create_article"),
            ("set_ticket_draft", {"body": "hi"}, "set_shared_draft"),
            ("update_ticket", {"title": "x"}, "update_ticket"),
            ("delete_ticket", {}, "delete_ticket"),
        ],
    )
    def test_ticket_in_forbidden_group_denied(
        self, client: Any, tool: str, kwargs: dict[str, Any], client_method: str
    ) -> None:
        from zammad_mcp_server import server

        with pytest.raises(PermissionError):
            getattr(server, tool)(ticket_id=2, **kwargs)
        getattr(client, client_method).assert_not_called()

    def test_ticket_in_allowed_group_permitted(self, client: Any) -> None:
        from zammad_mcp_server.server import get_ticket_articles

        client.get_ticket_articles.return_value = []
        assert get_ticket_articles(1)["count"] == 0

    def test_update_ticket_cannot_move_to_forbidden_group(self, client: Any) -> None:
        from zammad_mcp_server.server import update_ticket

        with pytest.raises(PermissionError, match="Admin"):
            update_ticket(ticket_id=1, group="Admin")
        client.update_ticket.assert_not_called()

    def test_create_ticket_in_forbidden_group_denied(self, client: Any) -> None:
        from zammad_mcp_server.server import create_ticket

        with pytest.raises(PermissionError, match="Admin"):
            create_ticket(title="x", group="Admin")
        client.create_ticket.assert_not_called()

    def test_ticket_resource_denied(self, client: Any) -> None:
        from zammad_mcp_server.server import get_ticket_resource

        with pytest.raises(PermissionError):
            get_ticket_resource("2")

    def test_get_ticket_stats(self, client: Any) -> None:
        from zammad_mcp_server.server import get_ticket_stats

        with pytest.raises(PermissionError):
            get_ticket_stats(group="Admin")

        get_ticket_stats()
        ticket_filter = client.get_ticket_stats.call_args.kwargs["ticket_filter"]
        assert ticket_filter({"group": "Support"})
        assert not ticket_filter({"group": "Admin"})

    def test_group_tools_hide_forbidden_groups(self, client: Any) -> None:
        from zammad_mcp_server.server import get_group, list_groups

        result = list_groups()
        assert [g["name"] for g in result["groups"]] == ["Support"]
        assert result["count"] == 1

        assert get_group(1)["name"] == "Support"
        with pytest.raises(PermissionError):
            get_group(2)


class TestPolicyVisibility:
    """Test that tools and resources outside the policy are hidden from clients."""

    @pytest.fixture
    def policy_env(self, monkeypatch: Any) -> None:
        from zammad_mcp_server import server

        monkeypatch.setenv("ZAMMAD_URL", "http://zammad.invalid")
        monkeypatch.setenv("ZAMMAD_HTTP_TOKEN", "x")
        monkeypatch.setenv("MCP_ALLOWED_CATEGORIES", "tickets,system")
        monkeypatch.setenv("MCP_DENIED_TOOLS", "create_ticket")
        monkeypatch.delenv("MCP_ALLOWED_GROUPS", raising=False)
        # The lifespan replaces these; monkeypatch restores them afterwards
        monkeypatch.setattr(server, "_client", None)
        monkeypatch.setattr(server, "_access_controller", None)

    async def test_only_allowed_components_listed(self, policy_env: None) -> None:
        from fastmcp import Client

        from zammad_mcp_server.server import mcp

        async with Client(mcp) as client:
            tools = {t.name for t in await client.list_tools()}
            templates = {t.uri_template for t in await client.list_resource_templates()}
            resources = {str(r.uri) for r in await client.list_resources()}

        assert tools == {
            "get_ticket", "search_tickets", "update_ticket", "get_ticket_articles",
            "create_article", "set_ticket_draft", "get_ticket_stats", "get_server_info",
            "get_allowed_tools",
        }
        assert templates == {"zammad://ticket/{ticket_id}"}
        assert resources == set()

    @pytest.mark.parametrize("tool", ["create_ticket", "delete_ticket", "get_user"])
    async def test_hidden_tools_cannot_be_called(self, policy_env: None, tool: str) -> None:
        from fastmcp import Client
        from fastmcp.exceptions import ToolError

        from zammad_mcp_server.server import mcp

        async with Client(mcp) as client:
            with pytest.raises(ToolError, match="Unknown tool"):
                await client.call_tool(tool, {})

    async def test_hidden_resource_cannot_be_read(self, policy_env: None) -> None:
        from fastmcp import Client

        from zammad_mcp_server.server import mcp

        async with Client(mcp) as client:
            with pytest.raises(Exception, match="not found"):
                await client.read_resource("zammad://user/1")

    async def test_everything_hidden_before_policy_loads(self, monkeypatch: Any) -> None:
        from zammad_mcp_server import server

        monkeypatch.setattr(server, "_access_controller", None)
        tools = await server.mcp.local_provider.list_tools()

        assert await server.PolicyVisibility().list_tools(tools) == []

    async def test_registered_components_have_policy_entries(self) -> None:
        """Every tool is categorised and every resource is gated by a tool."""
        from zammad_mcp_server.access_control import TOOL_CATEGORIES
        from zammad_mcp_server.server import RESOURCE_TOOLS, mcp

        tools = {t.name for t in await mcp.local_provider.list_tools()}
        resources = {str(r.uri) for r in await mcp.local_provider.list_resources()}
        templates = {t.uri_template for t in await mcp.local_provider.list_resource_templates()}

        assert tools == set(TOOL_CATEGORIES)
        assert resources | templates == set(RESOURCE_TOOLS)
        assert set(RESOURCE_TOOLS.values()) <= set(TOOL_CATEGORIES)


class TestDeniedToolEnforcement:
    """Regression: MCP_DENIED_TOOLS used to be ignored for WRITE-level tools."""

    def test_denied_write_tool_refused_on_call(self) -> None:
        from zammad_mcp_server.access_control import AccessController, AccessPolicy, Permission
        from zammad_mcp_server.server import create_ticket

        controller = AccessController(
            AccessPolicy(default_permission=Permission.WRITE, denied_tools={"create_ticket"})
        )
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller", return_value=controller):
            with pytest.raises(PermissionError, match="create_ticket"):
                create_ticket(title="x", group="Support")
            mock_get_client.return_value.create_ticket.assert_not_called()


class TestToolInfo:
    """Test suite for tool information."""

    def test_get_allowed_tools(self, unrestricted_controller: Any) -> None:
        """Test getting allowed tools information."""
        with patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:
            mock_get_controller.return_value = unrestricted_controller

            from zammad_mcp_server.server import get_allowed_tools
            result = get_allowed_tools()

            assert isinstance(result, list)
            assert len(result) > 0


class TestAccessControlIntegration:
    """Test suite for access control integration."""

    def test_read_only_cannot_create_ticket(self, read_only_controller: Any) -> None:
        """Test that read-only policy prevents ticket creation."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_get_client.return_value = MagicMock()
            mock_get_controller.return_value = read_only_controller

            from zammad_mcp_server.server import create_ticket
            with pytest.raises(PermissionError):
                create_ticket(title="Test", group="Support")

    def test_read_only_cannot_update_ticket(self, read_only_controller: Any) -> None:
        """Test that read-only policy prevents ticket updates."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_get_client.return_value = MagicMock()
            mock_get_controller.return_value = read_only_controller

            from zammad_mcp_server.server import update_ticket
            with pytest.raises(PermissionError):
                update_ticket(ticket_id=1, title="New Title")

    def test_read_only_cannot_create_article(self, read_only_controller: Any) -> None:
        """Test that read-only policy prevents article creation."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_get_client.return_value = MagicMock()
            mock_get_controller.return_value = read_only_controller

            from zammad_mcp_server.server import create_article
            with pytest.raises(PermissionError):
                create_article(ticket_id=1, body="New content")

    def test_read_only_can_search(self, read_only_controller: Any) -> None:
        """Test that read-only policy allows searching."""
        with patch("zammad_mcp_server.server.get_client") as mock_get_client, \
             patch("zammad_mcp_server.server.get_access_controller") as mock_get_controller:

            mock_client = MagicMock()
            mock_result = MagicMock()
            mock_result.items = []
            mock_result.total_count = 0
            mock_client.search_tickets.return_value = mock_result
            mock_get_client.return_value = mock_client
            mock_get_controller.return_value = read_only_controller

            from zammad_mcp_server.server import search_tickets
            result = search_tickets()

            assert "tickets" in result
