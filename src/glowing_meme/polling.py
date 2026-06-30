"""Async polling of Glowing Meme agents."""

import asyncio
import time
from datetime import datetime

import httpx

from .models import Machine, MachineState, Status


async def poll_machine(
    client: httpx.AsyncClient,
    machine: Machine,
    port: int,
    timeout: float,
) -> MachineState:
    """Poll a single agent and return its state."""
    state = MachineState(machine=machine)
    state.last_poll_attempt = datetime.now()
    url = f"http://{machine.tailscale_ip}:{port}/info"
    start = time.time()

    try:
        response = await client.get(url, timeout=timeout)
        state.latency_ms = round((time.time() - start) * 1000, 2)
        response.raise_for_status()
        data = response.json()
        state.info = data
        state.agent_version = data.get("version")
        state.last_poll_success = datetime.now()

        if state.agent_version is None:
            state.status = Status.AGENT_ERROR
            state.error = "agent response missing version"
        else:
            state.status = Status.HEALTHY
    except httpx.TimeoutException:
        state.status = Status.UNREACHABLE
        state.error = f"timeout after {timeout}s"
    except httpx.ConnectError as exc:
        state.status = Status.UNREACHABLE
        state.error = f"connection error: {exc}"
    except httpx.HTTPStatusError as exc:
        state.status = Status.AGENT_ERROR
        state.error = f"http error {exc.response.status_code}"
    except Exception as exc:
        state.status = Status.AGENT_ERROR
        state.error = f"unexpected error: {exc}"

    return state


async def poll_machines(
    machines: list[Machine],
    port: int,
    timeout: float,
) -> list[MachineState]:
    """Poll all *machines* concurrently."""
    async with httpx.AsyncClient() as client:
        tasks = [poll_machine(client, machine, port, timeout) for machine in machines]
        return list(await asyncio.gather(*tasks))
