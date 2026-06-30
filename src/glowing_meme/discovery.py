"""Discovery of monitored machines via the local Tailscale CLI."""

import json
import subprocess
from datetime import datetime
from typing import Any, Optional

from .models import Machine


def _run_tailscale_status() -> dict[str, Any]:
    """Run ``tailscale status --json`` and return the parsed output."""
    result = subprocess.run(
        ["tailscale", "status", "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _select_ip(addresses: list[str]) -> Optional[str]:
    """Prefer IPv4 Tailscale address, then IPv6."""
    ipv4: Optional[str] = None
    ipv6: Optional[str] = None
    for addr in addresses:
        if addr.startswith("100."):
            ipv4 = addr
        elif ":" in addr and ipv6 is None:
            ipv6 = addr
    return ipv4 or ipv6


def _node_to_machine(node_id: str, node: dict[str, Any], agent_tag: str) -> Optional[Machine]:
    tags = node.get("Tags") or []
    if agent_tag not in tags:
        return None

    tailscale_ips = node.get("TailscaleIPs") or []
    ip = _select_ip(tailscale_ips)
    if not ip:
        return None

    return Machine(
        device_id=node_id,
        name=node.get("Name", ""),
        hostname=node.get("HostName", ""),
        tailscale_ip=ip,
        tags=list(tags),
        online=bool(node.get("Online", False)),
        last_seen_by_tailscale=_parse_timestamp(node.get("LastSeen")),
    )


def discover_machines(agent_tag: str) -> list[Machine]:
    """Discover machines tagged with *agent_tag* from ``tailscale status --json``."""
    data = _run_tailscale_status()
    machines: list[Machine] = []

    peers = data.get("Peer") or {}
    for node_id, node in peers.items():
        machine = _node_to_machine(node_id, node, agent_tag)
        if machine:
            machines.append(machine)

    self_node = data.get("Self") or {}
    machine = _node_to_machine(self_node.get("ID", "self"), self_node, agent_tag)
    if machine:
        machines.append(machine)

    return machines
