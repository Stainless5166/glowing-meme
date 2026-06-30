"""Tests for Tailscale machine discovery."""

from unittest.mock import patch

import pytest

from glowing_meme.discovery import _select_ip, discover_machines
from glowing_meme.models import Machine


def test_select_ip_prefers_ipv4():
    assert _select_ip(["fd7a:115c:a1e0::1", "100.64.0.1"]) == "100.64.0.1"


def test_select_ip_falls_back_to_ipv6():
    assert _select_ip(["fd7a:115c:a1e0::1"]) == "fd7a:115c:a1e0::1"


def test_select_ip_returns_none_when_empty():
    assert _select_ip([]) is None


_SAMPLE_STATUS = {
    "Self": {
        "ID": "selfnode",
        "Name": "controller.example.com",
        "HostName": "controller",
        "TailscaleIPs": ["100.64.0.1"],
        "Tags": ["tag:glowing-meme-agent"],
        "Online": True,
        "LastSeen": "2026-06-30T15:00:00Z",
    },
    "Peer": {
        "abc123": {
            "Name": "machine1.example.com",
            "HostName": "machine1",
            "TailscaleIPs": ["100.64.0.2"],
            "Tags": ["tag:glowing-meme-agent"],
            "Online": True,
            "LastSeen": "2026-06-30T15:00:00Z",
        },
        "def456": {
            "Name": "machine2.example.com",
            "HostName": "machine2",
            "TailscaleIPs": ["100.64.0.3"],
            "Tags": ["tag:other"],
            "Online": True,
        },
    },
}


def test_discover_machines_filters_by_tag():
    with patch("glowing_meme.discovery._run_tailscale_status", return_value=_SAMPLE_STATUS):
        machines = discover_machines("tag:glowing-meme-agent")

    assert len(machines) == 2
    hostnames = {m.hostname for m in machines}
    assert hostnames == {"controller", "machine1"}


def test_discover_machines_sets_fields():
    with patch("glowing_meme.discovery._run_tailscale_status", return_value=_SAMPLE_STATUS):
        machines = discover_machines("tag:glowing-meme-agent")

    machine1 = next(m for m in machines if m.hostname == "machine1")
    assert machine1.device_id == "abc123"
    assert machine1.tailscale_ip == "100.64.0.2"
    assert machine1.online is True
    assert machine1.last_seen_by_tailscale is not None
