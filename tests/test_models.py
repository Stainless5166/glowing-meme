"""Tests for data models."""

from glowing_meme.models import Machine, MachineState, Status


def test_status_values():
    assert Status.HEALTHY.value == "healthy"
    assert Status.UNREACHABLE.value == "unreachable"
    assert Status.AGENT_ERROR.value == "agent_error"


def test_machine_defaults():
    machine = Machine(
        device_id="abc123",
        name="machine1.example.com",
        hostname="machine1",
        tailscale_ip="100.64.0.2",
        tags=["tag:glowing-meme-agent"],
    )
    assert machine.online is False
    assert machine.last_seen_by_tailscale is None


def test_machine_state_defaults():
    machine = Machine(
        device_id="abc123",
        name="machine1.example.com",
        hostname="machine1",
        tailscale_ip="100.64.0.2",
        tags=["tag:glowing-meme-agent"],
    )
    state = MachineState(machine=machine)
    assert state.status == Status.UNKNOWN
    assert state.info == {}
    assert state.error is None
