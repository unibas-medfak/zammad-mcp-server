"""Authentication for network transports.

The MCP specification expects remote servers to authenticate callers with a bearer
token in the ``Authorization`` header. This server verifies that token against a
fixed set configured by the operator: simple to run, but the tokens live in the
environment in plain text and cannot be revoked individually without a restart.

stdio transport is a local subprocess owned by the client, so it is never
authenticated; see ``require_auth_for_transport``.
"""

from __future__ import annotations

import json
import os
from typing import Any

import structlog
from fastmcp.server.auth import AuthProvider
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

logger = structlog.get_logger()

# Transports that expose the server over the network and therefore need auth.
NETWORK_TRANSPORTS = frozenset({"http", "streamable-http", "sse"})


class AuthConfigError(ValueError):
    """Raised when the authentication environment is incomplete or contradictory."""


def _csv_env(name: str) -> list[str]:
    """Read a comma-separated environment variable into a list of non-empty values."""
    return [value.strip() for value in os.getenv(name, "").split(",") if value.strip()]


def _parse_static_tokens(raw: str, default_scopes: list[str]) -> dict[str, dict[str, Any]]:
    """Parse ZAMMAD_MCP_AUTH_TOKENS into the mapping StaticTokenVerifier expects.

    Accepts either a JSON object mapping token -> claims, or the shorthand form
    ``client_id:token,other_client:other_token``.
    """
    raw = raw.strip()

    if raw.startswith("{"):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as e:
            raise AuthConfigError(f"ZAMMAD_MCP_AUTH_TOKENS is not valid JSON: {e}") from e
        if not isinstance(parsed, dict) or not parsed:
            raise AuthConfigError(
                "ZAMMAD_MCP_AUTH_TOKENS JSON must be a non-empty object mapping token to claims"
            )
        for token, claims in parsed.items():
            if not isinstance(claims, dict) or "client_id" not in claims:
                raise AuthConfigError(
                    f"ZAMMAD_MCP_AUTH_TOKENS entry for {token[:4]}... must be an object "
                    "containing at least client_id"
                )
            claims.setdefault("scopes", default_scopes)
        return parsed

    tokens: dict[str, dict[str, Any]] = {}
    for entry in _csv_env("ZAMMAD_MCP_AUTH_TOKENS"):
        client_id, separator, token = entry.partition(":")
        if not separator or not client_id.strip() or not token.strip():
            raise AuthConfigError(
                "ZAMMAD_MCP_AUTH_TOKENS entries must be 'client_id:token' pairs "
                "(or a JSON object mapping token to claims)"
            )
        tokens[token.strip()] = {"client_id": client_id.strip(), "scopes": default_scopes}

    if not tokens:
        raise AuthConfigError("ZAMMAD_MCP_AUTH=static requires ZAMMAD_MCP_AUTH_TOKENS to be set")
    return tokens


def build_auth_provider() -> AuthProvider | None:
    """Build the auth provider described by the environment.

    Returns None when ZAMMAD_MCP_AUTH is unset or "none", which leaves the server
    unauthenticated. Network transports refuse to start in that state unless the
    operator opts out explicitly; see require_auth_for_transport.
    """
    mode = os.getenv("ZAMMAD_MCP_AUTH", "none").strip().lower()
    required_scopes = _csv_env("ZAMMAD_MCP_AUTH_REQUIRED_SCOPES")

    if mode in ("", "none"):
        return None

    if mode == "static":
        tokens = _parse_static_tokens(os.getenv("ZAMMAD_MCP_AUTH_TOKENS", ""), required_scopes)
        logger.info("auth_configured", mode="static", token_count=len(tokens))
        return StaticTokenVerifier(tokens=tokens, required_scopes=required_scopes or None)

    raise AuthConfigError(f"Unknown ZAMMAD_MCP_AUTH mode {mode!r}; expected one of: none, static")


def require_auth_for_transport(transport: str, provider: AuthProvider | None) -> None:
    """Refuse to serve an unauthenticated server over the network.

    stdio is a local subprocess owned by the MCP client, so it needs no token. Any
    network transport without a provider is an open door to the Zammad credentials
    this server holds, so it fails closed unless the operator sets
    ZAMMAD_MCP_ALLOW_UNAUTHENTICATED=true.
    """
    if transport not in NETWORK_TRANSPORTS or provider is not None:
        return

    if os.getenv("ZAMMAD_MCP_ALLOW_UNAUTHENTICATED", "").strip().lower() == "true":
        logger.warning(
            "serving_without_authentication",
            transport=transport,
            detail="Every caller that can reach this port acts with the server's Zammad "
            "credentials. Restrict network access accordingly.",
        )
        return

    raise AuthConfigError(
        f"Refusing to serve transport {transport!r} without authentication. Set "
        "ZAMMAD_MCP_AUTH=static to require a bearer token, or set "
        "ZAMMAD_MCP_ALLOW_UNAUTHENTICATED=true if the port is already protected "
        "by other means."
    )
