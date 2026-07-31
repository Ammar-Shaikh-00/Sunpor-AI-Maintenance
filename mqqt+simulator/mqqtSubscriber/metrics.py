"""Prometheus metrics for MQTT subscriber (optional HTTP /metrics endpoint)."""
from __future__ import annotations

import logging
import os
import time

logger = logging.getLogger(__name__)

_started = False

try:
    from prometheus_client import Counter, Gauge, start_http_server

    MQTT_SUBSCRIBER_CONNECTED = Gauge(
        "sunpor_mqtt_subscriber_connected",
        "1 when the subscriber is connected to the MQTT broker, else 0",
    )
    MQTT_MESSAGES_RECEIVED = Counter(
        "sunpor_mqtt_messages_received_total",
        "MQTT messages received on subscribed topics",
        ["topic"],
    )
    MQTT_LAST_MESSAGE_TIMESTAMP = Gauge(
        "sunpor_mqtt_last_message_timestamp_seconds",
        "Unix timestamp of the last MQTT message received on a subscribed topic",
    )
    _PROMETHEUS_AVAILABLE = True
except ImportError:  # pragma: no cover - dev env without prometheus_client
    _PROMETHEUS_AVAILABLE = False


def start_metrics_server() -> None:
    """Start /metrics HTTP server if enabled. Never raises; does not block subscriber."""
    global _started

    if _started or not _PROMETHEUS_AVAILABLE:
        if not _PROMETHEUS_AVAILABLE:
            logger.debug("prometheus_client not installed; metrics disabled")
        return

    enabled = os.getenv("METRICS_ENABLED", "true").strip().lower()
    if enabled in {"0", "false", "no", "off"}:
        logger.info("MQTT metrics disabled (METRICS_ENABLED=%s)", os.getenv("METRICS_ENABLED"))
        return

    port = int(os.getenv("METRICS_PORT", "9101"))
    try:
        start_http_server(port)
        _started = True
        logger.info("Prometheus metrics listening on :%s/metrics", port)
    except OSError as exc:
        logger.warning("Could not start metrics server on port %s: %s", port, exc)


def set_connected(connected: bool) -> None:
    if not _PROMETHEUS_AVAILABLE:
        return
    MQTT_SUBSCRIBER_CONNECTED.set(1 if connected else 0)


def record_message(topic: str) -> None:
    """Record any raw message received (before payload validation)."""
    if not _PROMETHEUS_AVAILABLE:
        return
    MQTT_MESSAGES_RECEIVED.labels(topic=topic).inc()
    MQTT_LAST_MESSAGE_TIMESTAMP.set(time.time())
