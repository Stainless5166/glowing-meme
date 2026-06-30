# Design Document

## Project Name

Glowing Meme

## Summary

Glowing Meme is a Linux monitor for tagged Tailscale machines. It discovers
machines by running `tailscale status --json` locally, filters devices by tag,
checks live connectivity over the Tailnet, and polls a small Python agent on
each monitored Linux machine.

## Primary Use Case

A technical operator wants to see whether specific Linux machines in a Tailnet
are online and healthy without logging into each machine manually.

## High-Level Architecture

```text
+---------------------+
| Linux Monitor CLI   |
| rich / Python       |
+----------+----------+
           |
           | tailscale status --json
           v
+---------------------+
| Tailscale Inventory |
+---------------------+

+---------------------+
| Linux Monitor CLI   |
+----------+----------+
           |
           | HTTP over Tailnet
           v
+---------------------+
| Python Agent        |
| aiohttp / psutil    |
+---------------------+
```

## Components

### Monitor CLI

Responsibilities:

- Read configuration.
- Discover machines via `tailscale status --json`.
- Filter machines by tag.
- Poll each machine's agent over Tailscale.
- Maintain current machine state.
- Display status in an in-place terminal UI.
- Surface failures clearly.

Non-responsibilities:

- Agent installation.
- Remote command execution.
- Full asset management.
- Collection of sensitive data.

### Tailscale Discovery Client

Responsibilities:

- Run `tailscale status --json` locally.
- Parse the peer and self node lists.
- Filter devices by tag.
- Return raw device data to the monitor service.
- Handle command errors and timeouts.

### Polling Service

Responsibilities:

- Convert Tailscale device data into poll targets.
- Poll `/health` or `/info` on each target.
- Apply timeouts.
- Record success, failure, latency, and last successful response.
- Avoid blocking the UI thread.

### Agent

Responsibilities:

- Expose `/health`.
- Expose `/info`.
- Return minimal operational data.
- Run under systemd.
- Run as a restricted service user.

### Terminal UI

Initial UI requirements:

- Show list of tagged machines.
- Show online/offline status from Tailscale.
- Show hostname.
- Show Tailscale IP.
- Show agent version.
- Show uptime.
- Show load.
- Show memory percentage.
- Show last successful poll time.
- Show error summary if offline or unhealthy.

The UI redraws in place using `rich.live.Live` rather than scrolling.

Future tray status (PySide6 desktop UI):

```text
Green: all monitored machines healthy
Amber: one or more machines unhealthy
Red: no machines healthy or discovery failure
Grey: monitor paused or not configured
```

## Data Flow

### Discovery Flow

```text
Timer fires
  -> Monitor runs tailscale status --json
  -> Receives device list
  -> Filters by tag:glowing-meme-agent
  -> Extracts Tailscale IPs
  -> Updates known device list
```

### Polling Flow

```text
Timer fires
  -> For each known device
  -> Call http://{tailscale_ip}:8787/info
  -> Parse JSON response
  -> Update machine status
  -> Refresh UI
```

## Polling Intervals

Recommended defaults:

```text
Device discovery interval: 120 seconds
Agent polling interval: 30 seconds
HTTP timeout: 3 seconds
```

These should be configurable.

## Configuration

Required monitor settings:

```text
GM_MONITOR_TAG
default: tag:glowing-meme-agent

GM_AGENT_PORT
default: 8787
```

Default values:

```text
GM_MONITOR_TAG=tag:glowing-meme-agent
GM_AGENT_PORT=8787
GM_DISCOVERY_INTERVAL_SECONDS=120
GM_POLL_INTERVAL_SECONDS=30
GM_HTTP_TIMEOUT_SECONDS=3
```

Agent settings:

```text
GM_AGENT_HOST=0.0.0.0
GM_AGENT_PORT=8787
```

## Device Identity

The monitor should use the Tailscale device ID as the stable identifier where
available.

Fallback order:

```text
1. Tailscale device ID
2. Tailscale node key
3. Tailscale machine key
4. Hostname plus Tailscale IP
```

## IP Address Selection

Devices may have multiple addresses.

Preferred order:

```text
1. IPv4 Tailscale address
2. IPv6 Tailscale address
```

The first implementation uses the first available address of each family, with
IPv4 preferred.

## State Model

Each monitored machine should have a state similar to:

```json
{
  "device_id": "string",
  "name": "string",
  "hostname": "string",
  "tailscale_ip": "100.x.y.z",
  "tags": ["tag:glowing-meme-agent"],
  "online": true,
  "discovered_at": "2026-06-30T15:00:00+00:00",
  "last_seen_by_tailscale": "2026-06-30T14:59:00+00:00",
  "last_poll_attempt": "2026-06-30T15:00:00+00:00",
  "last_poll_success": "2026-06-30T15:00:00+00:00",
  "status": "healthy",
  "latency_ms": 42,
  "agent_version": "0.1.0",
  "info": {},
  "error": null
}
```

Allowed status values:

```text
unknown
healthy
unreachable
agent_error
api_error
stale
```

## Error Handling

### Discovery Failure

The monitor should:

- Keep displaying the last known device list.
- Mark discovery status as failed.
- Continue polling previously known devices.
- Show a visible discovery error.

### Agent Timeout

The monitor should:

- Mark the device as unreachable.
- Preserve the last successful data.
- Store the error summary.
- Retry on the next polling interval.

### Invalid Agent JSON

The monitor should:

- Mark the device as `agent_error`.
- Store a parse error summary.
- Continue polling later.

### Missing Agent Version

The monitor should:

- Mark the device as degraded or `agent_error`.
- Continue showing basic connectivity if possible.

## Security Design

Security controls:

- Tailscale ACLs restrict access to the agent port.
- Local firewall restricts the agent port to `tailscale0`.
- Agent runs as an unprivileged system user.
- Agent has a restricted systemd sandbox.
- Agent exposes only fixed read-only endpoints.

The agent must not expose clinical or patient data.

## Privacy Design

The system collects operational metadata only.

Allowed data:

- Hostname.
- Tailscale IP.
- Agent version.
- Uptime.
- Load average.
- Memory usage.
- Root filesystem usage.
- Poll status.
- Error summary.

Disallowed data:

- Patient information.
- Appointment information.
- Billing records.
- User documents.
- Shell history.
- Environment secrets.
- Process command lines unless explicitly reviewed later.

## MVP Scope

The MVP is complete when:

- Agent can run under systemd.
- Agent responds to `/health` and `/info`.
- Monitor can list tagged devices from `tailscale status --json`.
- Monitor can poll all discovered agents.
- Terminal UI shows current status.
- Basic failure states are visible.
- Validation tests pass.

## Future Enhancements

Possible later additions:

- PySide6 desktop UI and tray widget.
- Tailscale Admin API discovery option.
- `.deb` and AppImage desktop packaging.
- Config UI.
- Desktop notifications.
- Historical status database.
- Prometheus export.
- Agent auto-update.
- Per-machine notes.
- Maintenance mode.
- Alert thresholds.
