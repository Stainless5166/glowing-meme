"""In-place terminal UI for the Glowing Meme monitor."""

from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.table import Table

from .models import MachineState, Status

_STATUS_STYLES = {
    Status.HEALTHY: "green",
    Status.UNREACHABLE: "red",
    Status.AGENT_ERROR: "yellow",
    Status.STALE: "yellow",
    Status.UNKNOWN: "grey",
    Status.API_ERROR: "red",
}


def _format_timestamp(value: Optional[datetime]) -> str:
    if value is None:
        return "-"
    return value.strftime("%H:%M:%S")


def _format_load(info: dict) -> str:
    load = info.get("load", [])
    if not load or load == [-1.0, -1.0, -1.0]:
        return "-"
    return " ".join(f"{value:.2f}" for value in load)


def _format_percent(info: dict, key: str) -> str:
    section = info.get(key, {})
    percent = section.get("percent")
    if percent is None:
        return "-"
    return f"{percent}%"


def _format_duration(seconds: int) -> str:
    if seconds < 0:
        return "-"
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m"
    if seconds < 86400:
        return f"{seconds // 3600}h"
    return f"{seconds // 86400}d"


def render_table(states: list[MachineState], discovery_error: Optional[str] = None) -> Table:
    table = Table(title="Glowing Meme Monitor")
    table.add_column("Hostname")
    table.add_column("IP")
    table.add_column("Tailnet")
    table.add_column("Status")
    table.add_column("Version")
    table.add_column("Load")
    table.add_column("Mem")
    table.add_column("Disk")
    table.add_column("Agent Uptime")
    table.add_column("Last Poll")
    table.add_column("Error")

    for state in states:
        info = state.info
        style = _STATUS_STYLES.get(state.status, "white")
        table.add_row(
            state.machine.hostname or "-",
            state.machine.tailscale_ip,
            "online" if state.machine.online else "offline",
            state.status.value,
            state.agent_version or "-",
            _format_load(info),
            _format_percent(info, "memory"),
            _format_percent(info, "disk"),
            _format_duration(info.get("agent_uptime_seconds", -1)),
            _format_timestamp(state.last_poll_success),
            state.error or "",
            style=style,
        )

    if discovery_error:
        table.add_row()
        table.add_row(f"[red]Discovery error: {discovery_error}[/red]")

    return table


class MonitorUI:
    """Rich-based in-place terminal UI."""

    def __init__(self) -> None:
        self._console = Console()
        self._live: Optional[Live] = None

    def __enter__(self) -> "MonitorUI":
        self._live = Live(console=self._console, refresh_per_second=2)
        self._live.start()
        return self

    def __exit__(self, *args: object) -> None:
        if self._live:
            self._live.stop()

    def update(self, states: list[MachineState], discovery_error: Optional[str] = None) -> None:
        if self._live:
            self._live.update(render_table(states, discovery_error))
