"""Data models for the Glowing Meme monitor."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class Status(str, Enum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    UNREACHABLE = "unreachable"
    AGENT_ERROR = "agent_error"
    API_ERROR = "api_error"
    STALE = "stale"


@dataclass
class Machine:
    device_id: str
    name: str
    hostname: str
    tailscale_ip: str
    tags: list[str]
    online: bool = False
    discovered_at: datetime = field(default_factory=datetime.now)
    last_seen_by_tailscale: Optional[datetime] = None


@dataclass
class MachineState:
    machine: Machine
    last_poll_attempt: Optional[datetime] = None
    last_poll_success: Optional[datetime] = None
    status: Status = Status.UNKNOWN
    latency_ms: Optional[float] = None
    agent_version: Optional[str] = None
    info: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
