# Design Document

## Project Name

BM Tailnet Monitor

## Summary

BM Tailnet Monitor is a Linux desktop application that monitors tagged
Tailscale machines. It discovers machines through the Tailscale Admin API,
filters devices by tag, checks live connectivity over the Tailnet, and polls a
small Python agent on each monitored Linux machine.

## Primary Use Case

A technical operator wants to see whether specific Linux machines in a Tailnet
are online and healthy without logging into each machine manually.

## High-Level Architecture

```text
+---------------------+
| Linux Desktop App   |
| PySide6 / Python    |
+----------+----------+
           |
           | Tailscale Admin API
           v
+---------------------+
| Tailscale Inventory |
+---------------------+

+---------------------+
| Linux Desktop App   |
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

### Desktop Monitor

Responsibilities:

- Read configuration.
- Authenticate to the Tailscale Admin API.
- Fetch device inventory.
- Filter machines by tag.
- Poll each machine's agent over Tailscale.
- Maintain current machine state.
- Display status in a Linux desktop UI.
- Surface failures clearly.

Non-responsibilities:

- Agent installation.
- Remote command execution.
- Full asset management.
- Collection of sensitive data.

### Tailscale API Client

Responsibilities:

- List devices in the configured Tailnet.
- Return raw device data to the monitor service.
- Handle API errors and timeouts.

Expected API:

```text
GET /api/v2/tailnet/{tailnet}/devices
```

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

### Desktop UI

Initial UI requirements:

- Show list of tagged machines.
- Show online/offline status.
- Show hostname.
- Show Tailscale IP.
- Show agent version.
- Show uptime.
- Show load.
- Show memory percentage.
- Show last successful poll time.
- Show error summary if offline or unhealthy.

Optional tray status:

```text
Green: all monitored machines healthy
Amber: one or more machines unhealthy
Red: no machines healthy or API failure
Grey: monitor paused or not configured
```

## Data Flow

### Discovery Flow

```text
Timer fires
  -> Desktop app calls Tailscale Admin API
  -> Receives device list
  -> Filters by tag:monitor-agent
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

Required desktop settings:

```text
TAILSCALE_TAILNET
TAILSCALE_API_KEY
MONITOR_AGENT_TAG
MONITOR_AGENT_PORT
```

Default values:

```text
MONITOR_AGENT_TAG=tag:monitor-agent
MONITOR_AGENT_PORT=8787
DISCOVERY_INTERVAL_SECONDS=120
POLL_INTERVAL_SECONDS=30
HTTP_TIMEOUT_SECONDS=3
```

Agent settings:

```text
BM_AGENT_HOST=0.0.0.0
BM_AGENT_PORT=8787
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

The first implementation may use the first available address, but this should
be made explicit and tested.

## State Model

Each monitored machine should have a state similar to:

```json
{
  "device_id": "string",
  "name": "string",
  "hostname": "string",
  "tailscale_ip": "100.x.y.z",
  "tags": ["tag:monitor-agent"],
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

### Tailscale API Failure

The desktop app should:

- Keep displaying the last known device list.
- Mark discovery status as failed.
- Continue polling previously known devices.
- Show a visible API error.

### Agent Timeout

The desktop app should:

- Mark the device as unreachable.
- Preserve the last successful data.
- Store the error summary.
- Retry on the next polling interval.

### Invalid Agent JSON

The desktop app should:

- Mark the device as `agent_error`.
- Store a parse error summary.
- Continue polling later.

### Missing Agent Version

The desktop app should:

- Mark the device as degraded or `agent_error`.
- Continue showing basic connectivity if possible.

## Security Design

Security controls:

- Tailscale ACLs restrict access to the agent port.
- Local firewall restricts the agent port to `tailscale0`.
- Agent runs as an unprivileged system user.
- Agent has a restricted systemd sandbox.
- Agent exposes only fixed read-only endpoints.
- Desktop API key is stored securely where practical.

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
- Desktop app can list tagged devices from Tailscale.
- Desktop app can poll all discovered agents.
- Desktop UI shows current status.
- Basic failure states are visible.
- Validation tests pass.

## Future Enhancements

Possible later additions:

- `.deb` packaging.
- AppImage packaging.
- Config UI.
- Desktop notifications.
- Historical status database.
- Prometheus export.
- Agent auto-update.
- Per-machine notes.
- Maintenance mode.
- Alert thresholds.
