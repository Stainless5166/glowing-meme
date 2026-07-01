"""CLI entry point for the Glowing Meme monitor."""

import asyncio
import sys
from datetime import datetime
from typing import Optional

from .config import Config
from .discovery import discover_machines
from .models import MachineState
from .polling import poll_machines
from .ui_cli import MonitorUI


async def run_monitor(config: Config) -> None:
    """Main monitor loop: discover, poll, render."""
    known_states: dict[str, MachineState] = {}
    discovery_error: Optional[str] = None
    last_discovery: Optional[datetime] = None

    with MonitorUI(config.corporate_networks) as ui:
        while True:
            now = datetime.now()

            try:
                if (
                    last_discovery is None
                    or (now - last_discovery).seconds >= config.discovery_interval
                ):
                    machines = await asyncio.to_thread(discover_machines, config.agent_tag)
                    last_discovery = now
                    discovery_error = None

                    updated: dict[str, MachineState] = {}
                    for machine in machines:
                        existing = known_states.get(machine.device_id)
                        if existing:
                            existing.machine = machine
                            updated[machine.device_id] = existing
                        else:
                            updated[machine.device_id] = MachineState(machine=machine)
                    known_states = updated
            except Exception as exc:
                discovery_error = str(exc)

            states = list(known_states.values())
            if states:
                polled = await poll_machines(
                    [state.machine for state in states],
                    config.agent_port,
                    config.http_timeout,
                )
                for polled_state in polled:
                    known_states[polled_state.machine.device_id] = polled_state

            ui.update(list(known_states.values()), discovery_error)
            await asyncio.sleep(config.poll_interval)


def main() -> None:
    config = Config()
    try:
        asyncio.run(run_monitor(config))
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main()
