# Configuration

The Zammad MCP Server is configured through environment variables, set either in a `.env` file
or in the `env` block of your MCP client config.

> Based on the [Open Ticket AI configuration page](https://openticketai.com/en/docs/zammad-mcp-server/configuration/),
> checked against the code on 2026-09-23 and corrected where the two disagree.
> See [Differences from the website](#differences-from-the-website).

## Zammad connection

| Variable | Required | Description |
| --- | --- | --- |
| `ZAMMAD_URL` | Yes | Base URL of the Zammad instance, e.g. `https://helpdesk.example.com` |
| `ZAMMAD_HTTP_TOKEN` | One auth method | Personal access token (recommended) |
| `ZAMMAD_OAUTH2_TOKEN` | One auth method | OAuth2 bearer token |
| `ZAMMAD_USERNAME` / `ZAMMAD_PASSWORD` | One auth method | Basic auth, for legacy environments only |

If more than one method is set, `ZAMMAD_HTTP_TOKEN` wins.

### Creating a token

1. In Zammad, open **Profile → Token Access → Create**.
2. Enable **ticket.agent** (and **user_preferences** if you need profile reads).
3. Copy the secret straight away, because Zammad shows it only once.
4. Put it in `ZAMMAD_HTTP_TOKEN`.

## Access control

**The server fails closed.** If `MCP_ALLOWED_CATEGORIES` is unset or empty, every tool is denied.

| Variable | Default | Description |
| --- | --- | --- |
| `MCP_ALLOWED_CATEGORIES` | *(unset: deny all)* | Comma-separated categories that get **write** access: `tickets`, `users`, `organizations`, `groups`, `search`, `admin`, `system`, or `all` |
| `MCP_DENIED_TOOLS` | — | Comma-separated tool names to block, whatever their category |
| `MCP_ALLOWED_GROUPS` | *(all groups)* | Comma-separated Zammad group names. Tickets, articles, stats and groups outside these are hidden, and tickets in them can't be created, updated, deleted or moved into them |
| `MCP_ACCESS_LOG_MAX_ENTRIES` | `1000` | Number of entries kept in the in-memory access log (`0` disables it) |

### Permission levels

| Level | Behavior |
| --- | --- |
| `DENIED` | Calls to the tool are refused with a permission error |
| `READ_ONLY` | View data only |
| `WRITE` | Create and update |
| `ADMIN` | Also allows delete operations |

Categories listed in `MCP_ALLOWED_CATEGORIES` get `WRITE`, never `ADMIN`. So `delete_ticket`,
`delete_user` and `delete_organization` can't be called through environment configuration at all.
Keeping them in `MCP_DENIED_TOOLS` does no harm, and it keeps them blocked if that changes.

### Tool categories

| Category | Tools |
| --- | --- |
| `tickets` | `get_ticket`, `search_tickets`, `create_ticket`, `update_ticket`, `delete_ticket`, `get_ticket_articles`, `create_article`, `get_ticket_stats` |
| `users` | `get_user`, `search_users`, `create_user`, `update_user`, `delete_user`, `get_current_user` |
| `organizations` | `get_organization`, `search_organizations`, `create_organization`, `update_organization`, `delete_organization` |
| `groups` | `get_group`, `list_groups`, `create_group` |
| `admin` | `get_ticket_states`, `get_priorities` |
| `system` | `get_server_info` |

Call `get_allowed_tools` to see which tools the current policy allows.

### Policy recipes

**Read-only triage assistant** (search and summarize, no writes):

```env
MCP_ALLOWED_CATEGORIES=tickets,admin,system
MCP_DENIED_TOOLS=create_ticket,update_ticket,create_article
```

**Support lead** (search, summarize and add internal notes, limited to one group):

```env
MCP_ALLOWED_CATEGORIES=all
MCP_DENIED_TOOLS=delete_ticket,delete_user,delete_organization
MCP_ALLOWED_GROUPS=Support
```

**Full write automation** (use only with human review; deletes remain unavailable):

```env
MCP_ALLOWED_CATEGORIES=all
```

## Transport

| Flag | Environment variable | Default | Description |
| --- | --- | --- | --- |
| `--transport` | `ZAMMAD_MCP_TRANSPORT` | `stdio` | `stdio`, `http`, `streamable-http` or `sse` |
| `--host` | `ZAMMAD_MCP_HOST` | `127.0.0.1` | Bind address for network transports (`0.0.0.0` in Docker) |
| `--port` | `ZAMMAD_MCP_PORT` | `8000` | Port for network transports |

The Docker image runs `zammad-mcp-server --transport http --host 0.0.0.0 --port 8000` and serves
`GET /health` for its health check.

### Client authentication (network transports)

A network transport won't start without client authentication unless you explicitly opt out.

| Variable | Default | Description |
| --- | --- | --- |
| `ZAMMAD_MCP_AUTH` | `none` | `none` or `static` (bearer tokens) |
| `ZAMMAD_MCP_AUTH_TOKENS` | — | `client_id:token` pairs, or a JSON object mapping each token to its claims |
| `ZAMMAD_MCP_AUTH_REQUIRED_SCOPES` | — | Scopes every token must carry, e.g. `zammad:read,zammad:write` |
| `ZAMMAD_MCP_ALLOW_UNAUTHENTICATED` | — | Set to `true` to serve without auth when the port is already protected some other way |

See [DEPLOYMENT.md](DEPLOYMENT.md) for examples.

## Caching

Static Zammad metadata (groups, states and priorities) is cached in memory with a TTL, which cuts
API load. No configuration is needed.

## Logging

Structured JSON logging goes through `structlog`. Set the level with `LOG_LEVEL` (default `INFO`).

## Differences from the website

The website page (as of 2026-09-23) documents settings the code doesn't implement, and gets
some others wrong:

| Website says | Actual behaviour |
| --- | --- |
| `MCP_ALLOWED_CATEGORIES=all` is the default | Unset means **deny all** (fail closed) |
| `MCP_ALLOWED_ORGANIZATIONS=1,2` | Not read from the environment. The policy supports organization limits, but nothing sets them |
| `MCP_DEFAULT_PERMISSION=read_only` | Not implemented |
| `MCP_RATE_LIMIT_PER_MINUTE=60` | Not implemented: the policy has the field, but nothing reads or enforces it |
| `MCP_AUDIT_LOG_PATH` | Not implemented; access is only logged to stderr and the in-memory access log |
| `MCP_STRIP_HTML` / `body_plain` | Not implemented |
| `MCP_TRANSPORT`, `MCP_SERVER_HOST`, `MCP_SERVER_PORT` | Actually `ZAMMAD_MCP_TRANSPORT`, `ZAMMAD_MCP_HOST`, `ZAMMAD_MCP_PORT` |
| `MCP_SERVER_PATH` (`/mcp/`, `/sse/`) | Not configurable |
| `DENIED` tools are "not exposed to the client" | They're still listed; calling one returns a permission error |
| "Admin automation" recipe gives full write including deletes | Environment config never grants `ADMIN`, so deletes stay unavailable |
| Recipe uses the `search` category | No tools currently live in `search`; `get_ticket_states`/`get_priorities` are in `admin` |
| — | Not mentioned: `MCP_ACCESS_LOG_MAX_ENTRIES`, `LOG_LEVEL`, the `ZAMMAD_MCP_AUTH*` client-auth settings, and the `streamable-http` transport |
