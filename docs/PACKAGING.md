# Packaging

Glowing Meme is packaged as two separate packages:

- `glowing-meme-agent` — the small Python agent.
- `glowing-meme-monitor` — the terminal monitor.

Both Arch Linux (`PKGBUILD`) and Debian (`debian/`) packaging are provided.

## Quick Build

Install `uv`, then run:

```bash
make build-packages
```

The `scripts/build_packages.sh` script:

1. Reads the version from `git describe`.
2. Updates version strings in source and packaging files.
3. Runs the test suite.
4. Builds a Python wheel for the monitor.
5. Builds Arch and Debian packages.
6. Places all artifacts in `dist/`.

## Build Outputs

After a successful build, `dist/` contains:

```text
glowing-meme-agent-<version>-<arch>.pkg.tar.zst
glowing-meme-monitor-<version>-<arch>.pkg.tar.zst
glowing-meme-agent_<version>-<revision>_<arch>.deb
glowing-meme-monitor_<version>-<revision>_<arch>.deb
```

## Agent Package Contents

### Files

```text
/opt/glowing-meme-agent/agent.py
/usr/lib/systemd/system/glowing-meme-agent.service
```

### Runtime Dependencies

- `python3`
- `python3-aiohttp` / `python-aiohttp`
- `python3-psutil` / `python-psutil`
- `systemd`

### System User

The package creates an unprivileged system user:

```text
glowing-meme-agent
```

The user has no home directory and uses `/usr/sbin/nologin` as its shell.

### Service

Enable and start the agent:

```bash
sudo systemctl enable --now glowing-meme-agent.service
```

### Service Hardening

The systemd unit enables:

```text
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
```

## Monitor Package Contents

### Files

```text
/usr/bin/glowing-meme-monitor
/usr/bin/glowing-meme-monitor-launcher
/usr/share/applications/glowing-meme-monitor.desktop
```

The Python package is installed to the system Python `site-packages`.

### Runtime Dependencies

- `python3`
- `python3-httpx` / `python-httpx`
- `python3-rich` / `python-rich`
- `tailscale`

### Terminal Emulator

The `.desktop` file launches the monitor through `glowing-meme-monitor-launcher`,
which prefers `ghostty` and falls back to other common terminal emulators.

On Debian, `ghostty` is listed as a `Recommends`. On Arch, it is listed as an
`optdepends`.

### Autostart

Autostart is not enabled by default. To enable it for a user, copy the desktop
file:

```bash
cp /usr/share/applications/glowing-meme-monitor.desktop \
   ~/.config/autostart/
```

## Manual Packaging Steps

### Arch Linux

Agent:

```bash
cd packaging/agent
cp ../../agent/agent.py .
cp ../../agent/glowing-meme-agent.service .
makepkg -sf
```

Monitor:

```bash
cd packaging/monitor
uv build --wheel ../../
cp ../../dist/*.whl ./glowing-meme-monitor.whl
makepkg -sf
```

### Debian

Agent:

```bash
cd packaging/agent
cp ../../agent/agent.py .
cp ../../agent/glowing-meme-agent.service .
dpkg-buildpackage -us -uc -b
```

Monitor:

```bash
cd packaging/monitor
uv build --wheel ../../
cp ../../dist/*.whl ./glowing-meme-monitor.whl
dpkg-buildpackage -us -uc -b
```

## Post-install Firewall

After installing the agent, restrict port `8787/tcp` to the Tailscale interface.

### ufw

```bash
sudo ufw allow in on tailscale0 to any port 8787 proto tcp
sudo ufw deny 8787/tcp
```

Verify with:

```bash
sudo ufw status verbose
```

### Tailscale ACLs

Restrict access so only the monitor machine(s) can reach the agents:

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["tag:glowing-meme-controller"],
      "dst": ["tag:glowing-meme-agent:8787"]
    }
  ]
}
```

Replace `src` with the tag or user identity of the machine running the monitor.

> **Status:** Tailscale ACLs and local firewall rules are configured for this
> deployment.

## Versioning

Versions are derived from git tags:

- Tag `v0.1.0` → package version `0.1.0`.
- Five commits after `v0.1.0` → `0.1.0.dev5+g<hash>`.

Arch `pkgver` replaces `-` and `+` with `.` because `makepkg` does not allow
hyphens in package versions.

Debian versions use `~` for prereleases so they sort before the corresponding
release version.
