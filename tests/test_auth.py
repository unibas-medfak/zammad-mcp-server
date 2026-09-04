"""Tests for authentication configuration."""

from __future__ import annotations

import json

import pytest
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

from zammad_mcp_server.auth import (
    AuthConfigError,
    build_auth_provider,
    require_auth_for_transport,
)

AUTH_ENV_VARS = [
    "ZAMMAD_MCP_AUTH",
    "ZAMMAD_MCP_AUTH_TOKENS",
    "ZAMMAD_MCP_AUTH_REQUIRED_SCOPES",
    "ZAMMAD_MCP_ALLOW_UNAUTHENTICATED",
]


@pytest.fixture(autouse=True)
def clean_auth_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure no ambient auth configuration leaks between tests."""
    for name in AUTH_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


class TestBuildAuthProvider:
    """Tests for build_auth_provider."""

    def test_defaults_to_no_auth(self) -> None:
        assert build_auth_provider() is None

    def test_explicit_none_returns_no_auth(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZAMMAD_MCP_AUTH", "none")
        assert build_auth_provider() is None

    def test_unknown_mode_is_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZAMMAD_MCP_AUTH", "jwt")
        with pytest.raises(AuthConfigError, match="Unknown ZAMMAD_MCP_AUTH mode"):
            build_auth_provider()

    def test_mode_is_case_insensitive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZAMMAD_MCP_AUTH", "  STATIC  ")
        monkeypatch.setenv("ZAMMAD_MCP_AUTH_TOKENS", "claude:tok-a")
        assert isinstance(build_auth_provider(), StaticTokenVerifier)


class TestStaticMode:
    """Tests for ZAMMAD_MCP_AUTH=static."""

    def test_shorthand_pairs_are_parsed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZAMMAD_MCP_AUTH", "static")
        monkeypatch.setenv("ZAMMAD_MCP_AUTH_TOKENS", "claude:tok-a, cursor:tok-b")

        provider = build_auth_provider()

        assert isinstance(provider, StaticTokenVerifier)
        assert provider.tokens == {
            "tok-a": {"client_id": "claude", "scopes": []},
            "tok-b": {"client_id": "cursor", "scopes": []},
        }

    def test_scopes_are_attached_to_each_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZAMMAD_MCP_AUTH", "static")
        monkeypatch.setenv("ZAMMAD_MCP_AUTH_TOKENS", "claude:tok-a")
        monkeypatch.setenv("ZAMMAD_MCP_AUTH_REQUIRED_SCOPES", "zammad:read")

        provider = build_auth_provider()

        assert isinstance(provider, StaticTokenVerifier)
        assert provider.tokens["tok-a"]["scopes"] == ["zammad:read"]
        assert provider.required_scopes == ["zammad:read"]

    def test_json_form_is_parsed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZAMMAD_MCP_AUTH", "static")
        monkeypatch.setenv(
            "ZAMMAD_MCP_AUTH_TOKENS",
            json.dumps({"tok-a": {"client_id": "claude", "scopes": ["zammad:read"]}}),
        )

        provider = build_auth_provider()

        assert isinstance(provider, StaticTokenVerifier)
        assert provider.tokens["tok-a"]["scopes"] == ["zammad:read"]

    def test_json_entry_without_client_id_is_rejected(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ZAMMAD_MCP_AUTH", "static")
        monkeypatch.setenv("ZAMMAD_MCP_AUTH_TOKENS", json.dumps({"tok-a": {"scopes": []}}))
        with pytest.raises(AuthConfigError, match="client_id"):
            build_auth_provider()

    def test_invalid_json_is_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZAMMAD_MCP_AUTH", "static")
        monkeypatch.setenv("ZAMMAD_MCP_AUTH_TOKENS", "{not json")
        with pytest.raises(AuthConfigError, match="not valid JSON"):
            build_auth_provider()

    def test_missing_tokens_are_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZAMMAD_MCP_AUTH", "static")
        with pytest.raises(AuthConfigError, match="requires ZAMMAD_MCP_AUTH_TOKENS"):
            build_auth_provider()

    def test_malformed_pair_is_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZAMMAD_MCP_AUTH", "static")
        monkeypatch.setenv("ZAMMAD_MCP_AUTH_TOKENS", "tok-without-client")
        with pytest.raises(AuthConfigError, match="client_id:token"):
            build_auth_provider()


class TestRequireAuthForTransport:
    """Tests for the fail-closed guard on network transports."""

    @pytest.mark.parametrize("transport", ["http", "streamable-http", "sse"])
    def test_network_transport_without_auth_is_refused(self, transport: str) -> None:
        with pytest.raises(AuthConfigError, match="Refusing to serve"):
            require_auth_for_transport(transport, None)

    @pytest.mark.parametrize("transport", ["http", "streamable-http", "sse"])
    def test_network_transport_with_auth_is_allowed(self, transport: str) -> None:
        provider = StaticTokenVerifier(tokens={"t": {"client_id": "c", "scopes": []}})
        require_auth_for_transport(transport, provider)

    def test_stdio_without_auth_is_allowed(self) -> None:
        require_auth_for_transport("stdio", None)

    def test_explicit_opt_out_is_honored(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZAMMAD_MCP_ALLOW_UNAUTHENTICATED", "true")
        require_auth_for_transport("http", None)

    def test_opt_out_must_be_exactly_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZAMMAD_MCP_ALLOW_UNAUTHENTICATED", "1")
        with pytest.raises(AuthConfigError, match="Refusing to serve"):
            require_auth_for_transport("http", None)
