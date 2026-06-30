# Validation Tests

This document lists validation tests for BM Tailnet Monitor.

The MVP should not be considered complete until the required tests pass.

## Test Environment

Minimum test setup:

```text
1 Linux desktop/controller machine
2 Linux monitored machines
1 Tailnet
Tailscale tags configured
Tailscale ACLs configured
```

Required tags:

```text
tag:monitor-controller
tag:monitor-agent
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
sudo systemctl enable --now bm-monitor-agent.service
sudo systemctl status bm-monitor-agent.service
```

Expected result:

```text
Service is active.
Service restarts automatically after failure.
Service runs as bm-monitor-agent user.
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
HTTP 200 from controller machine.
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

1. Tag one machine with `tag:monitor-agent`.
2. Leave another machine untagged.
3. Run device discovery.

Expected result:

```text
Tagged machine appears in monitor.
Untagged machine does not appear in monitor.
```

Required: yes.

---

## 3. Tailscale API Tests

### 3.1 API key can list devices

Steps:

Call the Tailscale devices endpoint using the configured API key.

Expected result:

```text
HTTP 200.
Response contains devices.
```

Required: yes.

---

### 3.2 Invalid API key is handled

Steps:

Run monitor with an invalid API key.

Expected result:

```text
Application does not crash.
UI shows API authentication error.
Previously known device state is preserved if available.
```

Required: yes.

---

### 3.3 Tailscale API timeout is handled

Steps:

Simulate API timeout or block access to the Tailscale API.

Expected result:

```text
Application does not freeze.
Discovery error is shown.
Existing agents continue to be polled if already known.
```

Required: yes.

---

## 4. Desktop Monitor Tests

### 4.1 Application starts

Steps:

```bash
python -m bm_tailnet_monitor.app
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

Start the desktop app with valid Tailscale configuration.

Expected result:

```text
Machines tagged with MONITOR_AGENT_TAG appear in the UI.
```

Required: yes.

---

### 4.3 Healthy agent shown as healthy

Steps:

1. Ensure agent is running on a tagged machine.
2. Start desktop app.
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
sudo systemctl stop bm-monitor-agent.service
```

Expected result:

```text
Desktop app marks machine as unreachable after next poll.
Last successful data remains visible.
Error summary is shown.
```

Required: yes.

---

### 4.5 Agent restart is detected

Steps:

```bash
sudo systemctl restart bm-monitor-agent.service
```

Expected result:

```text
Desktop app returns machine to healthy on next successful poll.
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
Desktop app marks machine as unreachable.
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
Agent runs as bm-monitor-agent, not root.
```

Required: yes.

---

### 6.2 systemd hardening is enabled

Steps:

```bash
systemctl cat bm-monitor-agent.service
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

### 6.4 API key is not logged

Steps:

1. Start desktop app with a known test API key.
2. Trigger successful and failed API calls.
3. Inspect application logs.

Expected result:

```text
API key does not appear in logs.
```

Required: yes.

---

## 7. Acceptance Criteria

The MVP is accepted when:

```text
All required agent tests pass.
All required Tailscale/network tests pass.
All required desktop monitor tests pass.
All required data validation tests pass.
All required security tests pass.
```

## 8. Manual Test Record

Use this table during validation.

| Test ID | Result | Notes | Date | Tester |
|---|---:|---|---|---|
| 1.1 | Pending |  |  |  |
| 1.2 | Pending |  |  |  |
| 1.3 | Pending |  |  |  |
| 1.4 | Pending |  |  |  |
| 1.5 | Pending |  |  |  |
| 1.6 | Pending |  |  |  |
| 2.1 | Pending |  |  |  |
| 2.2 | Pending |  |  |  |
| 2.3 | Pending |  |  |  |
| 2.4 | Pending |  |  |  |
| 3.1 | Pending |  |  |  |
| 3.2 | Pending |  |  |  |
| 3.3 | Pending |  |  |  |
| 4.1 | Pending |  |  |  |
| 4.2 | Pending |  |  |  |
| 4.3 | Pending |  |  |  |
| 4.4 | Pending |  |  |  |
| 4.5 | Pending |  |  |  |
| 4.6 | Pending |  |  |  |
| 4.7 | Pending |  |  |  |
| 5.1 | Pending |  |  |  |
| 5.2 | Pending |  |  |  |
| 5.3 | Pending |  |  |  |
| 5.4 | Pending |  |  |  |
| 6.1 | Pending |  |  |  |
| 6.2 | Pending |  |  |  |
| 6.3 | Pending |  |  |  |
| 6.4 | Pending |  |  |  |
