# Agents

This document describes the small Python agent installed on monitored Linux
machines.

## Purpose

The agent exposes minimal operational information to the desktop monitor over
the Tailnet.

It is intentionally small.

The agent should answer:

- Is the machine reachable?
- Is the agent alive?
- What is the machine hostname?
- What is the uptime?
- What are basic load, memory, and disk statistics?
- What version of the agent is running?

The agent must not provide:

- Patient data.
- User documents.
- Environment secrets.
- Remote shell access.
- File browsing.
- Arbitrary command execution.

## Runtime

Recommended runtime:

```text
Python 3.11+
aiohttp
psutil
systemd
```

## Default Network Settings

```text
Host: 0.0.0.0
Port: 8787
Interface protection: tailscale0 firewall rule and Tailscale ACLs
```

The service may bind to `0.0.0.0` only if local firewall rules restrict access
to the Tailscale interface or equivalent network controls are used.

Preferred access path:

```text
Desktop monitor -> Tailscale IP -> Agent HTTP server
```

## Endpoints

### `GET /health`

Returns basic liveness information.

Required response fields:

```json
{
  "ok": true,
  "agent": "bm-monitor-agent",
  "version": "0.1.0",
  "timestamp": "2026-06-30T15:00:00+00:00"
}
```

### `GET /info`

Returns minimal machine information.

Required response fields:

```json
{
  "hostname": "machine-name",
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

## systemd Service

Suggested service name:

```text
bm-monitor-agent.service
```

Suggested unit file:

```ini
[Unit]
Description=BM Monitor Agent
After=network-online.target tailscaled.service
Wants=network-online.target

[Service]
Type=simple
User=bm-monitor-agent
Group=bm-monitor-agent
Environment=BM_AGENT_HOST=0.0.0.0
Environment=BM_AGENT_PORT=8787
ExecStart=/opt/bm-monitor-agent/.venv/bin/python /opt/bm-monitor-agent/agent.py
Restart=always
RestartSec=5

NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/tmp

[Install]
WantedBy=multi-user.target
```

## Installation Path

Recommended path:

```text
/opt/bm-monitor-agent/
```

Recommended files:

```text
/opt/bm-monitor-agent/agent.py
/opt/bm-monitor-agent/.venv/
/etc/systemd/system/bm-monitor-agent.service
```

## Agent User

Create a dedicated system user:

```bash
sudo useradd \
  --system \
  --no-create-home \
  --shell /usr/sbin/nologin \
  bm-monitor-agent
```

## Firewall

For `ufw`:

```bash
sudo ufw allow in on tailscale0 to any port 8787 proto tcp
sudo ufw deny 8787/tcp
```

Tailscale ACLs should also restrict access:

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

## Versioning

The agent must expose its version from both endpoints.

Version format:

```text
MAJOR.MINOR.PATCH
```

Example:

```text
0.1.0
```

## Logging

Logs should be minimal and should not include sensitive data.

Acceptable log fields:

- Startup time.
- Bind host.
- Bind port.
- Request path.
- Error summary.

Do not log:

- Tailscale API keys.
- User files.
- Environment variables.
- Patient or clinical data.

## Failure Behaviour

If data cannot be collected, the endpoint should still return a valid JSON
response where possible.

Example:

```json
{
  "ok": false,
  "agent": "bm-monitor-agent",
  "version": "0.1.0",
  "error": "unable to read disk statistics",
  "timestamp": "2026-06-30T15:00:00+00:00"
}
```

## Security Rules

The agent must not implement:

- Remote command execution.
- Arbitrary file reads.
- Arbitrary file writes.
- Software installation.
- User session inspection.
- Screenshot capture.
- Keyboard/mouse monitoring.

If tempted, make tea instead.
