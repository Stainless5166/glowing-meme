# Glowing Meme

A Linux-native monitor for tagged Tailscale machines.

The monitor runs on a Tailnet-connected Linux machine, discovers other machines
using the local `tailscale status --json` command, and polls a small Python
agent running on each tagged Linux machine.

## Goals

- Monitor tagged Tailscale machines.
- Show online/offline status.
- Poll a lightweight agent for minimal operational information.
- Run as a Linux terminal application (with a desktop UI as a future option).
- Keep the agent small, boring, and auditable.

## Non-goals

- No patient, clinical, or sensitive business data collection.
- No remote command execution.
- No general-purpose fleet management.
- No dependency on public network exposure.
- No Tailscale Admin API required for the MVP.

## Components

```text
Monitor CLI
  |
  | tailscale status --json
  v
Tailscale Device Inventory

Monitor CLI
  |
  | HTTP over Tailnet
  v
Glowing Meme Agent on Linux Machines
```

## Repository Layout

```text
glowing-meme/
  README.md
  AGENTS.md
  docs/
    DESIGN.md
    VALIDATION_TESTS.md
    PACKAGING.md
  src/glowing_meme/
    app.py
    config.py
    discovery.py
    models.py
    polling.py
    ui_cli.py
  agent/
    agent.py
    glowing-meme-agent.service
  packaging/
    agent/
    monitor/
  scripts/build_packages.sh
```

## Technology Choices

### Monitor

- Python 3.11+
- `uv` for dependency management
- `httpx` for agent polling
- `rich` for the in-place terminal UI
- `PySide6` for a future desktop UI

### Agent

- Python 3.11+
- `aiohttp`
- `psutil`
- `systemd` service

## Tailscale Tags

Recommended tags:

```text
tag:glowing-meme-agent
```

Machines running the agent should use:

```text
tag:glowing-meme-agent
```

The monitor itself must run on a Tailnet-connected machine with the Tailscale
CLI installed.

## Agent API

Default port:

```text
8787/tcp
```

Endpoints:

```text
GET /health
GET /info
```

Example health response:

```json
{
  "ok": true,
  "agent": "glowing-meme-agent",
  "version": "0.1.0",
  "timestamp": "2026-06-30T15:00:00+00:00"
}
```

Example info response:

```json
{
  "hostname": "reception-01",
  "agent": "glowing-meme-agent",
  "version": "0.1.0",
  "uptime_seconds": 123456,
  "agent_uptime_seconds": 120,
  "load": [0.12, 0.18, 0.21],
  "memory": {
    "total": 16728629248,
    "used": 5432152064,
    "available": 11296477184,
    "percent": 32.5
  },
  "disk": {
    "/": {
      "total": 250685575168,
      "used": 81234587648,
      "free": 169451987520,
      "percent": 32.4
    }
  },
  "timestamp": "2026-06-30T15:00:00+00:00"
}
```

## Configuration

### Agent

The agent supports:

```text
GM_AGENT_HOST
GM_AGENT_PORT
```

Example:

```bash
export GM_AGENT_HOST="0.0.0.0"
export GM_AGENT_PORT="8787"
```

### Monitor

The monitor supports:

```text
GM_MONITOR_TAG
default: tag:glowing-meme-agent

GM_AGENT_PORT
default: 8787

GM_DISCOVERY_INTERVAL_SECONDS
default: 120

GM_POLL_INTERVAL_SECONDS
default: 30

GM_HTTP_TIMEOUT_SECONDS
default: 3
```

## Development Setup

Install `uv`, then create the environment:

```bash
uv sync --all-extras
```

This installs the monitor, agent, desktop, and development dependencies.

## Running the Agent Manually

```bash
python agent/agent.py
```

Then test:

```bash
curl http://127.0.0.1:8787/health
curl http://127.0.0.1:8787/info
```

## Running the Monitor CLI

The monitor must run on a machine that is connected to the Tailnet and has the
Tailscale CLI installed.

```bash
glowing-meme-monitor
```

Or from the source tree:

```bash
python -m glowing_meme.app
```

The terminal UI redraws in place, showing discovered machines and their status.

## Formatting

Format all Python code with `black`:

```bash
make fmt
```

## Tests

```bash
make test
```

## Packaging

Build all packages:

```bash
make build-packages
```

This produces Arch Linux packages and Debian packages in `dist/`.

See `docs/PACKAGING.md` for detailed packaging instructions.

## Security Principles

- Access to the agent must be limited to the Tailnet.
- Tailscale ACLs should restrict access to `tag:glowing-meme-agent:8787`.
- The agent must not expose sensitive data.
- The agent must not execute remote commands.
- Logs should be minimal.
