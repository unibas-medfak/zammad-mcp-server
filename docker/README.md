# Local Zammad stack for MCP development

Docker Compose runs a **Zammad instance** next to your machine so you can test the
MCP server without touching production. The stack also includes the MCP server
itself (`zammad-mcp-server`), built from the repo's root `Dockerfile`, so you can
point Claude at `http://localhost:8000/mcp` for local testing.

## Quick start

```bash
cp .env.example .env
docker compose up -d zammad-postgresql zammad-redis zammad-elasticsearch zammad-init zammad-railsserver zammad-nginx
```

Open `http://localhost:8080` after 2–3 minutes. Default login:
`admin@example.com` / `admin`.

Create an API token under **Profile → Token Access**, paste it into `.env` as
`ZAMMAD_HTTP_TOKEN`, then start the MCP server:

```bash
docker compose up -d --build zammad-mcp-server
```

It listens on `http://localhost:8000`, guarded by the bearer token in
`MCP_CLIENT_TOKEN` (`.env`, defaults to `local-dev-token`). Point Claude at it:

```json
{
  "mcpServers": {
    "zammad": {
      "url": "http://localhost:8000/mcp",
      "headers": { "Authorization": "Bearer local-dev-token" }
    }
  }
}
```

### Using Podman instead of Docker

The compose file runs unchanged under Podman — swap `docker compose` for
`podman compose` (or `docker-compose` if that's what's on your `PATH`) in every
command above:

```bash
podman compose up -d zammad-postgresql zammad-redis zammad-elasticsearch zammad-init zammad-railsserver zammad-nginx
# ... create the token in Zammad, set ZAMMAD_HTTP_TOKEN in .env, then:
podman compose up -d --build zammad-mcp-server
```

Podman builds images in OCI format, which drops the Dockerfile's `HEALTHCHECK`
directive (harmless — `podman compose` still starts the container, it just won't
poll `/health` on its own). Pass `--format docker` to `podman build` instead if
you want the healthcheck kept.

## Choose a Zammad version

Set `ZAMMAD_VERSION` in `.env`:

| Tag | Purpose |
| --- | --- |
| `7.1` | **Default** — current release, primary test target |
| `7.0` | Match a 7.0 instance |
| `6.5` | Last supported 6.x line |
| `6.3` | Legacy 6.x checks |

Example:

```env
ZAMMAD_VERSION=6.5
```

The MCP server package itself is the same for all tags — only the local Zammad
container changes.

**Switching major versions:** stop the stack and remove volumes if migrations fail:

```bash
docker compose down -v
docker compose up -d
```

Full compatibility matrix:
[docs/COMPATIBILITY.md](../docs/COMPATIBILITY.md)
