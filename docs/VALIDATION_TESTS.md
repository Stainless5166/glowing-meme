# Validation Tests

This document lists validation tests for Glowing Meme.

The MVP should not be considered complete until the required tests pass.

## Test Environment

Minimum test setup:

```text
1 Linux monitor machine on the Tailnet
2 Linux monitored machines on the Tailnet
1 Tailnet
Tailscale tags configured
Tailscale ACLs configured
```

Required tag:

```text
tag:glowing-meme-agent
```

Default agent port:

```text
8787/tcp
```

## 1. Agent Tests

### 1.1 Agent starts manually

Steps:

```bash
python agent/agent.py
```

Expected result:

```text
Agent starts without crashing.
Agent listens on configured host and port.
```

Required: yes.

---

### 1.2 `/health` returns valid JSON

Steps:

```bash
curl http://127.0.0.1:8787/health
```

Expected result:

```text
HTTP 200.
Response is valid JSON.
Response contains ok, agent, version, and timestamp.
ok is true.
```

Required: yes.

---

### 1.3 `/info` returns valid JSON

Steps:

```bash
curl http://127.0.0.1:8787/info
```

Expected result:

```text
HTTP 200.
Response is valid JSON.
Response contains hostname, uptime_seconds, load, memory, disk, and timestamp.
```

Required: yes.

---

### 1.4 Agent exposes version

Steps:

```bash
curl http://127.0.0.1:8787/health
curl http://127.0.0.1:8787/info
```

Expected result:

```text
Both endpoints include the same agent version.
Version uses MAJOR.MINOR.PATCH format.
```

Required: yes.

---

### 1.5 Agent runs under systemd

Steps:

```bash
sudo systemctl enable --now glowing-meme-agent.service
sudo systemctl status glowing-meme-agent.service
```

Expected result:

```text
Service is active.
Service restarts automatically after failure.
Service runs as glowing-meme-agent user.
```

Required: yes.

---

### 1.6 Agent has no remote execution endpoint

Steps:

```bash
curl -i http://127.0.0.1:8787/exec
curl -i http://127.0.0.1:8787/shell
curl -i http://127.0.0.1:8787/run
```

Expected result:

```text
Each request returns HTTP 404 or 405.
No command is executed.
```

Required: yes.

---

## 2. Network and Tailscale Tests

### 2.1 Agent reachable over Tailscale IP

Steps:

```bash
curl http://100.x.y.z:8787/health
```

Expected result:

```text
HTTP 200 from monitor machine.
Valid health response.
```

Required: yes.

---

### 2.2 Agent not reachable from unauthorised source

Steps:

From a machine not allowed by Tailscale ACLs:

```bash
curl --max-time 5 http://100.x.y.z:8787/health
```

Expected result:

```text
Connection fails or times out.
```

Required: yes.

---

### 2.3 Local firewall restricts agent port

Steps:

Attempt to connect to the monitored machine's LAN IP:

```bash
curl --max-time 5 http://LAN_IP:8787/health
```

Expected result:

```text
Connection fails unless LAN access has been explicitly approved.
```

Required: yes.

---

### 2.4 Tailscale tag filtering works

Steps:

1. Tag one machine with `tag:glowing-meme-agent`.
2. Leave another machine untagged.
3. Run device discovery.

Expected result:

```text
Tagged machine appears in monitor.
Untagged machine does not appear in monitor.
```

Required: yes.

---

## 3. Tailscale Discovery Tests

### 3.1 `tailscale status --json` can list devices

Steps:

Run the monitor discovery on a Tailnet-connected machine.

Expected result:

```text
Discovery returns devices.
Tagged devices are present.
```

Required: yes.

---

### 3.2 Missing Tailscale CLI is handled

Steps:

Run the monitor on a machine without the Tailscale CLI, or temporarily rename
`tailscale`.

Expected result:

```text
Application does not crash.
UI shows discovery error.
Previously known device state is preserved if available.
```

Required: yes.

---

### 3.3 Tailscale discovery timeout is handled

Steps:

Simulate a slow or hanging `tailscale status --json` call.

Expected result:

```text
Application does not freeze.
Discovery error is shown.
Existing agents continue to be polled if already known.
```

Required: yes.

---

## 4. Monitor Tests

### 4.1 Application starts

Steps:

```bash
glowing-meme-monitor
```

Expected result:

```text
Application starts.
No unhandled exception is printed.
Configuration errors are shown clearly.
```

Required: yes.

---

### 4.2 Tagged devices are discovered

Steps:

Start the monitor on a Tailnet-connected machine.

Expected result:

```text
Machines tagged with GM_MONITOR_TAG appear in the UI.
```

Required: yes.

---

### 4.3 Healthy agent shown as healthy

Steps:

1. Ensure agent is running on a tagged machine.
2. Start monitor.
3. Wait for polling interval.

Expected result:

```text
Machine status is healthy.
Hostname, IP, version, uptime, load, and memory are displayed.
```

Required: yes.

---

### 4.4 Stopped agent shown as unreachable

Steps:

```bash
sudo systemctl stop glowing-meme-agent.service
```

Expected result:

```text
Monitor marks machine as unreachable after next poll.
Last successful data remains visible.
Error summary is shown.
```

Required: yes.

---

### 4.5 Agent restart is detected

Steps:

```bash
sudo systemctl restart glowing-meme-agent.service
```

Expected result:

```text
Monitor returns machine to healthy on next successful poll.
Agent uptime resets.
Machine uptime does not reset.
```

Required: yes.

---

### 4.6 Machine offline is detected

Steps:

Power off or disconnect a monitored machine.

Expected result:

```text
Monitor marks machine as unreachable.
UI remains responsive.
No crash.
```

Required: yes.

---

### 4.7 UI remains responsive during polling

Steps:

1. Configure at least two monitored machines.
2. Block one machine from responding.
3. Interact with the UI during polling.

Expected result:

```text
UI remains responsive.
Polling timeout does not block the UI thread.
```

Required: yes.

---

## 5. Data Validation Tests

### 5.1 No sensitive data in agent response

Steps:

Inspect `/health` and `/info` responses.

Expected result:

```text
No patient data.
No billing data.
No user documents.
No environment variables.
No shell history.
No process command lines.
```

Required: yes.

---

### 5.2 Memory values are plausible

Steps:

Compare `/info` memory output to:

```bash
free -b
```

Expected result:

```text
Values are broadly consistent.
memory.percent is between 0 and 100.
```

Required: yes.

---

### 5.3 Disk values are plausible

Steps:

Compare `/info` disk output to:

```bash
df -B1 /
```

Expected result:

```text
Values are broadly consistent.
disk["/"].percent is between 0 and 100.
```

Required: yes.

---

### 5.4 Uptime value is plausible

Steps:

Compare `/info` uptime to:

```bash
cat /proc/uptime
```

Expected result:

```text
uptime_seconds is broadly consistent with system uptime.
```

Required: yes.

---

## 6. Security Tests

### 6.1 Agent service runs as restricted user

Steps:

```bash
ps aux | grep agent.py
```

Expected result:

```text
Agent runs as glowing-meme-agent, not root.
```

Required: yes.

---

### 6.2 systemd hardening is enabled

Steps:

```bash
systemctl cat glowing-meme-agent.service
```

Expected result:

```text
NoNewPrivileges=true is present.
PrivateTmp=true is present.
ProtectSystem=strict is present.
ProtectHome=true is present.
```

Required: yes.

---

### 6.3 Agent port is not publicly exposed

Steps:

From outside the Tailnet, attempt to connect to the agent port.

Expected result:

```text
Connection fails.
```

Required: yes.

---

### 6.4 No secrets logged

Steps:

1. Start monitor with known configuration.
2. Trigger successful and failed discovery and polling.
3. Inspect application logs.

Expected result:

```text
No sensitive configuration values appear in logs.
```

Required: yes.

---

## 7. Acceptance Criteria

The MVP is accepted when:

```text
All required agent tests pass.
All required Tailscale/network tests pass.
All required monitor tests pass.
All required data validation tests pass.
All required security tests pass.
```

## 8. Manual Test Record

Use this table during validation.

| Test ID | Result | Notes | Date | Tester |
|---|---|---|---|---|
| 1.1 | Pass | Service active on Quartz6F, rebecca, cygnus | 2026-07-01 | opencode |
| 1.2 | Pass | Valid JSON from all reachable agents | 2026-07-01 | opencode |
| 1.3 | Pass | Valid JSON from all reachable agents | 2026-07-01 | opencode |
| 1.4 | Pass | Version 0.1.0 on deployed agents | 2026-07-01 | opencode |
| 1.5 | Pass | systemd service enabled and active | 2026-07-01 | opencode |
| 1.6 | Pass | /exec, /shell, /run return 404 | 2026-07-01 | opencode |
| 2.1 | Partial | Reachable on Quartz6F, rebecca, halitea0; BMG-Consolidate and cygnus timeout | 2026-07-01 | opencode |
| 2.2 | Not tested | Requires access from unauthorised Tailnet source | 2026-07-01 | opencode |
| 2.3 | Not tested | Requires LAN IP access to test | 2026-07-01 | opencode |
| 2.4 | Pass | 5 machines tagged with tag:glowing-meme-agent discovered | 2026-07-01 | opencode |
| 3.1 | Pass | tailscale status --json returns tagged devices | 2026-07-01 | opencode |
| 3.2 | Not tested |  | 2026-07-01 | opencode |
| 3.3 | Not tested |  | 2026-07-01 | opencode |
| 4.1 | Pass | glowing-meme-monitor starts without error | 2026-07-01 | opencode |
| 4.2 | Pass | 5 tagged machines appear in monitor | 2026-07-01 | opencode |
| 4.3 | Pass | Quartz6F, rebecca, halitea0 shown healthy | 2026-07-01 | opencode |
| 4.4 | Pass | Quartz6F marked unreachable after stop | 2026-07-01 | opencode |
| 4.5 | Pass | Quartz6F returns to healthy after restart | 2026-07-01 | opencode |
| 4.6 | Not tested | Requires powering off a monitored machine | 2026-07-01 | opencode |
| 4.7 | Pass | UI redraws in place during polling | 2026-07-01 | opencode |
| 5.1 | Pass | No patient, billing, secret, or env data in responses | 2026-07-01 | opencode |
| 5.2 | Pass | Memory values consistent with free -b | 2026-07-01 | opencode |
| 5.3 | Pass | Disk values consistent with df -B1 / | 2026-07-01 | opencode |
| 5.4 | Pass | Uptime consistent with /proc/uptime | 2026-07-01 | opencode |
| 6.1 | Pass | Agent runs as glowing-meme-agent user | 2026-07-01 | opencode |
| 6.2 | Pass | NoNewPrivileges, PrivateTmp, ProtectSystem, ProtectHome present | 2026-07-01 | opencode |
| 6.3 | Not tested | Requires access from outside the Tailnet | 2026-07-01 | opencode |
| 6.4 | Pass | Logs contain only paths and error summaries | 2026-07-01 | opencode |
