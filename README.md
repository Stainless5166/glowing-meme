# BM Tailnet Monitor

A Linux-native desktop monitor for tagged Tailscale machines.

The desktop application discovers machines in a Tailnet using the Tailscale
Admin API, filters them by tag, checks connection status, and polls a small
Python agent running on each active Linux machine.

## Goals

- Monitor tagged Tailscale machines.
- Show online/offline status.
- Poll a lightweight agent for minimal operational information.
- Run as a Linux desktop application or tray widget.
- Keep the agent small, boring, and auditable.

## Non-goals

- No patient, clinical, or sensitive business data collection.
- No remote command execution.
- No general-purpose fleet management.
- No dependency on public network exposure.

## Components

```text
Desktop Monitor
  |
  | Tailscale Admin API
  v
Tailscale Device Inventory

Desktop Monitor
  |
  | HTTP over Tailnet
  v
Python Agent on Linux Machines
```

## Repository Layout

```text
bm-tailnet-monitor/
  README.md
  AGENTS.md
  docs/
    DESIGN.md
    VALIDATION_TESTS.md
  src/
    bm_tailnet_monitor/
      app.py
      tailscale.py
      polling.py
      models.py
      ui_qt.py
  agent/
    agent.py
    bm-monitor-agent.service
```

## Initial Technology Choices

### Desktop application

- Python 3.11+
- PySide6
- httpx
- asyncio

### Agent

- Python 3.11+
- aiohttp
- psutil
- systemd

## Tailscale Tags

Recommended tags:

```text
tag:monitor-controller
tag:monitor-agent
```

The desktop monitor machine should use:

```text
tag:monitor-controller
```

Machines running the agent should use:

```text
tag:monitor-agent
```

## Tailscale ACL Example

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["tag:monitor-controller"],
      "dst": ["tag:monitor-agent:8787"]
    }
  ]
}
```

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
  "agent": "bm-monitor-agent",
  "version": "0.1.0",
  "timestamp": "2026-06-30T15:00:00+00:00"
}
```

Example info response:

```json
{
  "hostname": "reception-01",
  "agent": "bm-monitor-agent",
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

The desktop app requires:

```text
TAILSCALE_TAILNET
TAILSCALE_API_KEY
MONITOR_AGENT_TAG
MONITOR_AGENT_PORT
```

Example:

```bash
export TAILSCALE_TAILNET="example.com"
export TAILSCALE_API_KEY="tskey-api-..."
export MONITOR_AGENT_TAG="tag:monitor-agent"
export MONITOR_AGENT_PORT="8787"
```

The agent supports:

```text
BM_AGENT_HOST
BM_AGENT_PORT
```

Example:

```bash
export BM_AGENT_HOST="0.0.0.0"
export BM_AGENT_PORT="8787"
```

## Development Setup

Create a virtual environment:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -U pip
```

Install desktop dependencies:

```bash
pip install PySide6 httpx
```

Install agent dependencies:

```bash
pip install aiohttp psutil
```

## Running the Agent Manually

```bash
python agent/agent.py
```

Then test:

```bash
curl http://127.0.0.1:8787/health
curl http://127.0.0.1:8787/info
```

## Running the Desktop Monitor

Initial CLI mode should be implemented before the full desktop UI.

Example future command:

```bash
python -m bm_tailnet_monitor.app
```

## Packaging Targets

Preferred first targets:

- Agent: `.deb` package plus systemd service.
- Desktop monitor: `.deb` or AppImage.

Flatpak can be considered later if useful.

## Security Principles

- Access to the agent must be limited to the Tailnet.
- Tailscale ACLs should restrict access to `tag:monitor-controller`.
- The agent must not expose sensitive data.
- The agent must not execute remote commands.
- The desktop Tailscale API key must be treated as secret.
- Logs should be minimal.
