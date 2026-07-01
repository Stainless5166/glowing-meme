"""Tests for the Glowing Meme agent."""

import pytest
from aiohttp.test_utils import TestClient, TestServer

import agent


@pytest.fixture
async def client():
    app = agent.create_app()
    server = TestServer(app)
    client = TestClient(server)
    await client.start_server()
    yield client
    await client.close()


async def test_health_returns_valid_json(client):
    resp = await client.get("/health")
    assert resp.status == 200
    data = await resp.json()
    assert data["ok"] is True
    assert data["agent"] == "glowing-meme-agent"
    assert data["version"] == agent.VERSION
    assert "timestamp" in data


async def test_info_returns_valid_json(client):
    resp = await client.get("/info")
    assert resp.status == 200
    data = await resp.json()
    assert "hostname" in data
    assert data["agent"] == "glowing-meme-agent"
    assert data["version"] == agent.VERSION
    assert "uptime_seconds" in data
    assert "agent_uptime_seconds" in data
    assert "load" in data
    assert "memory" in data
    assert "disk" in data
    assert "interfaces" in data
    assert "timestamp" in data


async def test_info_interfaces_are_present(client):
    resp = await client.get("/info")
    data = await resp.json()
    interfaces = data.get("interfaces", [])
    assert isinstance(interfaces, list)
    if interfaces:
        iface = interfaces[0]
        assert "name" in iface
        assert "type" in iface
        assert "addresses" in iface
        assert "is_up" in iface


async def test_version_matches_across_endpoints(client):
    health = await (await client.get("/health")).json()
    info = await (await client.get("/info")).json()
    assert health["version"] == info["version"]
    parts = health["version"].split(".")
    assert len(parts) == 3


async def test_unknown_paths_return_404(client):
    for path in ["/exec", "/shell", "/run", "/arbitrary"]:
        resp = await client.get(path)
        assert resp.status == 404, path
        data = await resp.json()
        assert data["ok"] is False


async def test_info_contains_no_sensitive_data(client):
    resp = await client.get("/info")
    data = await resp.json()
    payload = str(data).lower()
    forbidden = ["password", "secret", "token", "patient", "clinical"]
    for word in forbidden:
        assert word not in payload, f"unexpected sensitive word: {word}"
    assert "API_KEY" not in str(data)
