#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
./ops/dc config --quiet
./ops/dc run --rm --no-deps --entrypoint promtool prometheus check config /etc/prometheus/prometheus.yml
./ops/dc run --rm --no-deps --entrypoint promtool prometheus check rules /etc/prometheus/rules.yml
./ops/dc run --rm --no-deps loki -config.file=/etc/loki/loki.yml -verify-config=true
./ops/dc run --rm --no-deps alloy validate /etc/alloy/config.alloy
./ops/dc run --rm --no-deps docker-socket-proxy haproxy -c -f /usr/local/etc/haproxy/haproxy.cfg

./ops/dc run --rm --no-deps --entrypoint amtool alertmanager check-config /etc/alertmanager/alertmanager.yml
