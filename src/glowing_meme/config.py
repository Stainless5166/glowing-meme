"""Configuration for the Glowing Meme monitor."""

import ipaddress
import os
from typing import Iterable


class Config:
    """Monitor configuration loaded from environment variables."""

    def __init__(self) -> None:
        self.agent_tag = os.environ.get("GM_MONITOR_TAG", "tag:glowing-meme-agent")
        self.agent_port = int(os.environ.get("GM_AGENT_PORT", "8787"))
        self.discovery_interval = int(os.environ.get("GM_DISCOVERY_INTERVAL_SECONDS", "120"))
        self.poll_interval = int(os.environ.get("GM_POLL_INTERVAL_SECONDS", "30"))
        self.http_timeout = float(os.environ.get("GM_HTTP_TIMEOUT_SECONDS", "3"))
        self.corporate_networks = _parse_cidrs(os.environ.get("GM_CORPORATE_NETWORKS", ""))


def _parse_cidrs(value: str) -> Iterable[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    if not value:
        return []
    networks = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            networks.append(ipaddress.ip_network(item, strict=False))
        except ValueError:
            continue
    return networks
