"""Tests for agent polling."""

import httpx
import pytest

from glowing_meme.models import Machine, Status
from glowing_meme.polling import poll_machine


@pytest.fixture
def sample_machine():
    return Machine(
        device_id="abc123",
        name="machine1.example.com",
        hostname="machine1",
        tailscale_ip="100.64.0.2",
        tags=["tag:glowing-meme-agent"],
        online=True,
    )


async def test_poll_machine_healthy(sample_machine):
    def handler(request):
        return httpx.Response(
            200,
            json={
                "version": "0.1.0",
                "hostname": "machine1",
                "load": [0.1, 0.2, 0.3],
                "memory": {"percent": 32.5},
                "disk": {"/": {"percent": 24.0}},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        state = await poll_machine(client, sample_machine, 8787, 3.0)

    assert state.status == Status.HEALTHY
    assert state.agent_version == "0.1.0"
    assert state.last_poll_success is not None
    assert state.error is None


async def test_poll_machine_missing_version(sample_machine):
    def handler(request):
        return httpx.Response(200, json={"hostname": "machine1"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        state = await poll_machine(client, sample_machine, 8787, 3.0)

    assert state.status == Status.AGENT_ERROR
    assert "version" in (state.error or "").lower()


async def test_poll_machine_timeout(sample_machine):
    def handler(request):
        raise httpx.TimeoutException("timed out")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        state = await poll_machine(client, sample_machine, 8787, 0.01)

    assert state.status == Status.UNREACHABLE
    assert "timeout" in (state.error or "").lower()


async def test_poll_machine_connection_error(sample_machine):
    def handler(request):
        raise httpx.ConnectError("connection refused")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        state = await poll_machine(client, sample_machine, 8787, 3.0)

    assert state.status == Status.UNREACHABLE
    assert "connection" in (state.error or "").lower()


async def test_poll_machine_http_error(sample_machine):
    def handler(request):
        return httpx.Response(500, text="internal error")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        state = await poll_machine(client, sample_machine, 8787, 3.0)

    assert state.status == Status.AGENT_ERROR
    assert "500" in (state.error or "")
