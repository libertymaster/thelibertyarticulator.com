import os

bind = "0.0.0.0:8000"
workers = int(os.environ.get("GUNICORN_WORKERS", "2"))
threads = int(os.environ.get("GUNICORN_THREADS", "2"))
worker_class = "gthread"
timeout = 60
graceful_timeout = 45
keepalive = 5
max_requests = 1200
max_requests_jitter = 120
accesslog = "-"
# No query strings, cookies, Access assertions, or authorization headers in access logs.
access_log_format = '%(h)s %(m)s %(U)s %(s)s %(L)s'
errorlog = "-"
capture_output = True
forwarded_allow_ips = ""
limit_request_line = 4094
limit_request_fields = 100

def child_exit(server, worker):
    from prometheus_client import multiprocess
    if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
        multiprocess.mark_process_dead(worker.pid)

# The container root filesystem is intentionally read-only.
# Gunicorn 25.1+ enables a Unix control socket by default. We do not use
# gunicornc, so disable it rather than providing another writable path.
control_socket_disable = True
