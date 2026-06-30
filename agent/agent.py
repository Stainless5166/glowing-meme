#!/usr/bin/env python3
"""Glowing Meme agent.

A small read-only HTTP agent that exposes minimal operational information
about the Linux machine it runs on. It must not expose sensitive data,
execute remote commands, or perform arbitrary file reads.
"""

import logging
import os
import time
from datetime import datetime, timezone

import aiohttp.web
import psutil

AGENT = "glowing-meme-agent"
VERSION = "0.1.0"

HOST = os.environ.get("GM_AGENT_HOST", "0.0.0.0")
PORT = int(os.environ.get("GM_AGENT_PORT", "8787"))

_START_TIME = time.time()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
_logger = logging.getLogger("glowing-meme-agent")


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@aiohttp.web.middleware
async def _request_logger(request: aiohttp.web.Request, handler):
    _logger.info("%s %s", request.method, request.path)
    try:
        return await handler(request)
    except Exception as exc:  # pragma: no cover - defensive logging
        _logger.error("Error handling %s: %s", request.path, exc)
        raise


async def health(request: aiohttp.web.Request) -> aiohttp.web.Response:
    return aiohttp.web.json_response(
        {
            "ok": True,
            "agent": AGENT,
            "version": VERSION,
            "timestamp": _iso_now(),
        }
    )


async def info(request: aiohttp.web.Request) -> aiohttp.web.Response:
    try:
        hostname = os.uname().nodename
    except Exception:  # pragma: no cover - defensive
        hostname = "unknown"

    try:
        uptime_seconds = int(time.time() - psutil.boot_time())
    except Exception:  # pragma: no cover - defensive
        uptime_seconds = -1

    try:
        load1, load5, load15 = os.getloadavg()
        load = [round(load1, 2), round(load5, 2), round(load15, 2)]
    except Exception:  # pragma: no cover - defensive
        load = [-1.0, -1.0, -1.0]

    try:
        mem = psutil.virtual_memory()
        memory = {
            "total": mem.total,
            "used": mem.used,
            "available": mem.available,
            "percent": round(mem.percent, 1),
        }
    except Exception:  # pragma: no cover - defensive
        memory = {}

    try:
        disk = psutil.disk_usage("/")
        disk_data = {
            "/": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": round(disk.percent, 1),
            }
        }
    except Exception:  # pragma: no cover - defensive
        disk_data = {}

    return aiohttp.web.json_response(
        {
            "hostname": hostname,
            "agent": AGENT,
            "version": VERSION,
            "uptime_seconds": uptime_seconds,
            "agent_uptime_seconds": int(time.time() - _START_TIME),
            "load": load,
            "memory": memory,
            "disk": disk_data,
            "timestamp": _iso_now(),
        }
    )


async def _not_found(request: aiohttp.web.Request) -> aiohttp.web.Response:
    return aiohttp.web.json_response(
        {"ok": False, "agent": AGENT, "version": VERSION, "error": "not found"},
        status=404,
    )


def create_app() -> aiohttp.web.Application:
    app = aiohttp.web.Application(middlewares=[_request_logger])
    app.router.add_get("/health", health)
    app.router.add_get("/info", info)
    app.router.add_route("*", "/{path:.*}", _not_found)
    return app


def main() -> None:
    app = create_app()
    _logger.info("Starting %s v%s on %s:%s", AGENT, VERSION, HOST, PORT)
    aiohttp.web.run_app(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
