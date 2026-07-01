"""Full-terminal dashboard for the Glowing Meme monitor."""

import ipaddress
from typing import Any, Iterable, Optional

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from . import __version__ as monitor_version
from .models import MachineState, Status

_STATUS_GLYPHS = {
    Status.HEALTHY: ("●", "green"),
    Status.UNREACHABLE: ("●", "red"),
    Status.AGENT_ERROR: ("●", "yellow"),
    Status.STALE: ("●", "yellow"),
    Status.UNKNOWN: ("○", "grey"),
    Status.API_ERROR: ("●", "red"),
}

_ERROR_GLYPHS = {
    "timeout": ("⏱", "yellow"),
    "connection error": ("✕", "red"),
    "agent_error": ("⚠", "yellow"),
    "unreachable": ("✕", "red"),
}


def _status_glyph(state: MachineState) -> Text:
    if not state.machine.online and state.status != Status.HEALTHY:
        return Text("○", style="grey")
    glyph, style = _STATUS_GLYPHS.get(state.status, ("?", "white"))
    return Text(glyph, style=style)


def _connection_glyph(interfaces: list[dict[str, Any]]) -> Text:
    types = {iface.get("type") for iface in interfaces if iface.get("is_up")}
    has_wifi = "wifi" in types
    has_ethernet = "ethernet" in types

    if has_wifi and has_ethernet:
        return Text("W+E", style="cyan")
    if has_wifi:
        return Text("W", style="cyan")
    if has_ethernet:
        return Text("E", style="blue")
    return Text("-", style="grey")


def _corporate_info(
    interfaces: list[dict[str, Any]],
    networks: Iterable[ipaddress.IPv4Network | ipaddress.IPv6Network],
) -> Text:
    if not networks:
        return Text("-", style="grey")

    for iface in interfaces:
        if iface.get("type") in ("tailscale", "loopback"):
            continue
        if not iface.get("is_up"):
            continue
        for addr in iface.get("addresses", []):
            try:
                ip = ipaddress.ip_address(addr.split("%", 1)[0])
            except ValueError:
                continue
            for network in networks:
                if ip.version == network.version and ip in network:
                    return Text(f"✓ {addr}", style="green")

    return Text("✗", style="red")


def _version_style(agent_version: Optional[str]) -> str:
    if agent_version is None:
        return "grey"
    if "+" in agent_version or "dev" in agent_version.lower():
        return "blue"
    if agent_version == monitor_version:
        return "green"
    return "red"


def _format_duration(seconds: int) -> str:
    if seconds < 0:
        return "-"
    if seconds < 3600:
        return f"{seconds // 60}m"
    if seconds < 86400:
        return f"{seconds // 3600}h"
    return f"{seconds // 86400}d"


def _format_bytes(value: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if value < 1024:
            return f"{value:.1f}{unit}"
        value /= 1024
    return f"{value:.1f}PB"


def _format_mem(info: dict[str, Any]) -> Text:
    section = info.get("memory", {})
    total = section.get("total")
    used = section.get("used")
    percent = section.get("percent")
    if total is None or used is None or percent is None:
        return Text("-", style="grey")
    style = "green" if percent < 70 else "yellow" if percent < 90 else "red"
    return Text(
        f"{_format_bytes(used)} / {_format_bytes(total)} ({percent}%)",
        style=style,
    )


def _format_disk(info: dict[str, Any]) -> Text:
    section = info.get("disk", {}).get("/", {})
    total = section.get("total")
    used = section.get("used")
    percent = section.get("percent")
    if total is None or used is None or percent is None:
        return Text("-", style="grey")
    style = "green" if percent < 70 else "yellow" if percent < 90 else "red"
    return Text(
        f"{_format_bytes(used)} / {_format_bytes(total)} ({percent}%)",
        style=style,
    )


def _format_load(info: dict[str, Any]) -> Text:
    load = info.get("load", [])
    cpu_count = info.get("cpu_count", 0)
    if not load or load == [-1.0, -1.0, -1.0] or cpu_count is None or cpu_count <= 0:
        return Text("-", style="grey")

    load1, load5, load15 = load
    percent = min((load1 / cpu_count) * 100, 999)
    style = "green" if percent < 70 else "yellow" if percent < 90 else "red"

    if load1 > load15:
        trend = ("▲", "red")
    elif load1 < load15:
        trend = ("▼", "green")
    else:
        trend = ("→", "grey")

    return Text.assemble(
        (f"{percent:.0f}%", style),
        " ",
        (trend[0], trend[1]),
        " ",
        (f"({load1:.1f}/{load5:.1f}/{load15:.1f})", "dim"),
    )


def _error_glyph(state: MachineState) -> Text:
    if not state.error:
        return Text("", style="green")
    error_lower = (state.error or "").lower()
    for key, (glyph, style) in _ERROR_GLYPHS.items():
        if key in error_lower:
            return Text(glyph, style=style)
    return Text("⚠", style="yellow")


def _render_table(
    states: list[MachineState],
    corporate_networks: Iterable[ipaddress.IPv4Network | ipaddress.IPv6Network],
) -> Table:
    table = Table(expand=True)
    table.add_column("Hostname", ratio=3, min_width=18)
    table.add_column("Conn", justify="center", width=4)
    table.add_column("Corp", ratio=2, min_width=10)
    table.add_column("Version", width=10)
    table.add_column("Uptime", width=8)
    table.add_column("Load", width=22)
    table.add_column("Mem", ratio=2, min_width=20)
    table.add_column("Disk", ratio=2, min_width=20)
    table.add_column("Err", width=4)

    for state in states:
        info = state.info
        interfaces = info.get("interfaces", [])
        hostname = Text.assemble(
            _status_glyph(state),
            " ",
            (state.machine.hostname or "-", _STATUS_GLYPHS.get(state.status, ("", "white"))[1]),
        )

        table.add_row(
            hostname,
            _connection_glyph(interfaces),
            _corporate_info(interfaces, corporate_networks),
            Text(state.agent_version or "-", style=_version_style(state.agent_version)),
            _format_duration(info.get("uptime_seconds", -1)),
            _format_load(info),
            _format_mem(info),
            _format_disk(info),
            _error_glyph(state),
        )

    return table


def _render_layout(
    states: list[MachineState],
    discovery_error: Optional[str],
    corporate_networks: Iterable[ipaddress.IPv4Network | ipaddress.IPv6Network],
) -> Layout:
    healthy = sum(1 for s in states if s.status == Status.HEALTHY)
    unreachable = sum(1 for s in states if s.status == Status.UNREACHABLE)
    errors = sum(1 for s in states if s.status == Status.AGENT_ERROR)
    unknown = sum(1 for s in states if s.status == Status.UNKNOWN)

    header_text = Text.assemble(
        ("Glowing Meme Monitor", "bold cyan"),
        "  ",
        (f"{healthy} healthy", "green"),
        "  ",
        (f"{unreachable} unreachable", "red"),
        "  ",
        (f"{errors} errors", "yellow"),
        "  ",
        (f"{unknown} unknown", "grey"),
    )
    header = Layout(Panel(header_text, expand=True), size=3)

    footer_text = Text("Ctrl-C to quit", style="dim")
    if discovery_error:
        footer_text = Text.assemble(
            ("Discovery error: ", "red"),
            (discovery_error, "red"),
            "    ",
            ("Ctrl-C to quit", "dim"),
        )
    footer = Layout(Panel(footer_text, expand=True), size=3)

    main = Layout(Panel(_render_table(states, corporate_networks), expand=True))

    layout = Layout()
    layout.split_column(header, main, footer)
    return layout


class MonitorUI:
    """Rich-based full-terminal dashboard."""

    def __init__(
        self,
        corporate_networks: Iterable[ipaddress.IPv4Network | ipaddress.IPv6Network],
    ) -> None:
        self._corporate_networks = corporate_networks
        self._console = Console()
        self._live: Optional[Live] = None

    def __enter__(self) -> "MonitorUI":
        self._live = Live(
            console=self._console,
            refresh_per_second=2,
            screen=True,
        )
        self._live.start()
        return self

    def __exit__(self, *args: object) -> None:
        if self._live:
            self._live.stop()

    def update(self, states: list[MachineState], discovery_error: Optional[str] = None) -> None:
        if self._live:
            self._live.update(_render_layout(states, discovery_error, self._corporate_networks))
