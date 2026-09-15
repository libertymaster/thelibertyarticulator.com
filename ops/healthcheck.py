#!/usr/bin/env python3
import sys
import time
from urllib.request import Request, urlopen

if len(sys.argv) != 2:
    raise SystemExit("usage: healthcheck.py {web|worker|beat}")

role = sys.argv[1]

if role == "web":
    request = Request(
        "http://127.0.0.1:8000/ready/",
        headers={"Host": "web"},
    )
    with urlopen(request, timeout=6) as response:
        if response.status != 200:
            raise SystemExit(1)

elif role == "worker":
    import socket

    from config.celery import app

    destination = "worker@" + socket.gethostname()
    reply = app.control.inspect(
        destination=[destination],
        timeout=5,
    ).ping()

    if not reply or reply.get(destination, {}).get("ok") != "pong":
        raise SystemExit(1)

elif role == "beat":
    import django

    django.setup()

    from django.core.cache import cache

    last = cache.get("scheduler_last_success")
    if last is None or time.time() - float(last) > 180:
        raise SystemExit(1)

else:
    raise SystemExit("Unknown health check")
