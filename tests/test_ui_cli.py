"""Tests for monitor UI formatting helpers."""

from glowing_meme.ui_cli import _format_bytes, _format_duration, _format_load


def test_format_bytes():
    assert "GB" in _format_bytes(16000000000)
    assert "MB" in _format_bytes(500000000)


def test_format_duration():
    assert _format_duration(45) == "45s" or _format_duration(45) == "0m"
    assert _format_duration(3600) == "1h"
    assert _format_duration(86400) == "1d"


def test_format_load_percentage_and_trend():
    info = {"cpu_count": 4, "load": [1.0, 2.0, 3.0]}
    text = _format_load(info)
    rendered = str(text)
    assert "%" in rendered
    assert "▼" in rendered  # load1 < load15


def test_format_load_missing_cpu_count():
    info = {"load": [1.0, 2.0, 3.0]}
    text = _format_load(info)
    assert str(text) == "-"
