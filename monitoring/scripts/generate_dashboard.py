#!/usr/bin/env python3
"""Generate SUNPOR Edge Grafana dashboard JSON."""
import json
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent.parent / "grafana" / "dashboards" / "sunpor-edge-overview.json"

# PromQL helpers — compatible with legacy prometheus (job=edge-s01) config.
NODE = 'job="$server", instance=~".*:9100"'
CADVISOR = 'job="$server", instance=~".*:8080"'
# cAdvisor container metrics — require name+image labels (needs docker.sock mounted).
DOCKER_LABELLED = 'name=~".+", image=~".+"'
CONTAINER_FILTER = DOCKER_LABELLED
CONTAINER_EXISTS = "container_last_seen"
CONTAINER_CPU = "container_cpu_usage_seconds_total"
CONTAINER_MEM = "container_memory_usage_bytes"
CONTAINER_NET_RX = "container_network_receive_bytes_total"
CONTAINER_NET_TX = "container_network_transmit_bytes_total"
# Fallback when cAdvisor is not linked to Docker API (overlay FS devices ≈ container count)
OVERLAY_FALLBACK = 'device=~"^overlay_.*", id="/"'


def svc_running_expr(svc_key: str) -> str:
    """Match Docker container via name, image, or compose labels."""
    rules = SERVICE_MATCH.get(svc_key, [f'name=~".*{svc_key}.*"'])
    base = f"{CONTAINER_EXISTS}{{{CADVISOR}, {DOCKER_LABELLED}"
    parts = [f"count({base}, {rule}}})" for rule in rules]
    return f"(({ ' or '.join(parts) })) or on() vector(0)"


def running_containers_expr() -> str:
    """Named containers when Docker linked; overlay device count as fallback."""
    named = (
        f"count(count by (name) "
        f"({CONTAINER_EXISTS}{{{CADVISOR}, {DOCKER_LABELLED}}}))"
    )
    overlay = (
        f"count(count by (device) "
        f"({CONTAINER_MEM}{{{CADVISOR}, {OVERLAY_FALLBACK}}}))"
    )
    return f"({named}) or ({overlay})"


def docker_linked_expr() -> str:
    return f"count({CONTAINER_EXISTS}{{{CADVISOR}, {DOCKER_LABELLED}}})"

# Match services by name and/or image (name label is often empty on cgroup v2)
SERVICE_MATCH: dict[str, list[str]] = {
    "sunpor-backend": [
        'name=~".*sunpor-backend.*"',
        'image=~".*backend-backend.*"',
        'container_label_com_docker_compose_service="backend"',
    ],
    "sunpor-timescaledb": [
        'name=~".*sunpor-timescaledb.*"',
        'image=~".*timescaledb.*"',
        'container_label_com_docker_compose_service=~"timescaledb|db"',
    ],
    "sunpor-mqtt": [
        'name=~".*sunpor-mqtt.*"',
        'image=~".*mosquitto.*"',
        'container_label_com_docker_compose_service="mqtt"',
    ],
    "sunpor-frontend": [
        'name=~".*sunpor-frontend.*"',
        'image=~".*frontend-frontend.*"',
        'container_label_com_docker_compose_service="frontend"',
    ],
    "mqtt-subscriber": [
        'name=~".*mqtt-subscriber.*"',
        'image=~".*mqqtsubscriber.*"',
        'container_label_com_docker_compose_service=~"mqtt-subscriber|subscriber"',
    ],
    "node-exporter": [
        'name=~".*node-exporter.*"',
        'image=~".*node-exporter.*"',
    ],
    "cadvisor": [
        'name=~".*cadvisor.*"',
        'image=~".*cadvisor.*"',
    ],
}


def container_cpu_rate() -> str:
    return f"rate({CONTAINER_CPU}{{{CADVISOR}, {CONTAINER_FILTER}}}[5m]) * 100"


def stat_panel(pid, title, expr, unit, x, y, w=4, h=4, thresholds=None, desc=""):
    if thresholds is None:
        thresholds = [
            {"color": "green", "value": None},
            {"color": "yellow", "value": 70},
            {"color": "red", "value": 85},
        ]
    return {
        "id": pid,
        "type": "stat",
        "title": title,
        "description": desc,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "datasource": {"type": "prometheus", "uid": "${datasource}"},
        "targets": [{"expr": expr, "refId": "A", "legendFormat": ""}],
        "fieldConfig": {
            "defaults": {
                "unit": unit,
                "decimals": 1,
                "color": {"mode": "thresholds"},
                "thresholds": {"mode": "absolute", "steps": thresholds},
            },
            "overrides": [],
        },
        "options": {
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "orientation": "auto",
            "textMode": "auto",
            "colorMode": "background",
            "graphMode": "area",
            "justifyMode": "center",
        },
    }


def timeseries_panel(pid, title, targets, x, y, w=12, h=8, unit="percent", desc=""):
    return {
        "id": pid,
        "type": "timeseries",
        "title": title,
        "description": desc,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "datasource": {"type": "prometheus", "uid": "${datasource}"},
        "targets": targets,
        "fieldConfig": {
            "defaults": {
                "unit": unit,
                "custom": {
                    "drawStyle": "line",
                    "lineInterpolation": "smooth",
                    "fillOpacity": 20,
                    "gradientMode": "opacity",
                    "showPoints": "never",
                    "spanNulls": False,
                },
                "color": {"mode": "palette-classic"},
            },
            "overrides": [],
        },
        "options": {
            "legend": {"displayMode": "table", "placement": "bottom", "calcs": ["mean", "max", "lastNotNull"]},
            "tooltip": {"mode": "multi", "sort": "desc"},
        },
    }


def row_panel(pid, title, y, collapsed=False):
    return {
        "id": pid,
        "type": "row",
        "title": title,
        "collapsed": collapsed,
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y},
        "panels": [],
    }


def table_panel(pid, title, expr, x, y, w=24, h=8):
    return {
        "id": pid,
        "type": "table",
        "title": title,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "datasource": {"type": "prometheus", "uid": "${datasource}"},
        "targets": [
            {
                "expr": expr,
                "refId": "A",
                "format": "table",
                "instant": True,
            }
        ],
        "fieldConfig": {"defaults": {}, "overrides": []},
        "options": {"showHeader": True, "sortBy": [{"displayName": "CPU %", "desc": True}]},
        "transformations": [
            {
                "id": "organize",
                "options": {
                    "excludeByName": {
                        "Time": True,
                        "__name__": True,
                        "id": True,
                        "instance": True,
                        "job": True,
                        "image": True,
                        "container_label_com_docker_compose_project": True,
                    },
                    "renameByName": {
                        "name": "Container",
                        "Value #CPU": "CPU %",
                        "Value #MEM": "Memory",
                        "Value #NET RX": "Net RX",
                        "Value #NET TX": "Net TX",
                    },
                },
            },
        ],
    }


def text_panel(pid, content, x, y, w=24, h=3):
    return {
        "id": pid,
        "type": "text",
        "title": "",
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "options": {
            "mode": "markdown",
            "content": content,
        },
    }


def gauge_panel(pid, title, expr, x, y, w=6, h=6):
    return {
        "id": pid,
        "type": "gauge",
        "title": title,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "datasource": {"type": "prometheus", "uid": "${datasource}"},
        "targets": [{"expr": expr, "refId": "A"}],
        "fieldConfig": {
            "defaults": {
                "unit": "percent",
                "min": 0,
                "max": 100,
                "thresholds": {
                    "mode": "absolute",
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "yellow", "value": 70},
                        {"color": "red", "value": 85},
                    ],
                },
            },
            "overrides": [],
        },
        "options": {
            "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
            "showThresholdLabels": False,
            "showThresholdMarkers": True,
        },
    }


panels = []
y = 0

# Header
panels.append(
    text_panel(
        1,
        "# SUNPOR Edge Infrastructure\n"
        "Select **Server** from the top bar. Host metrics use **node-exporter**; containers use **cAdvisor**.\n\n"
        "**If container panels show No data:** cAdvisor must mount `/var/run/docker.sock`. "
        "Check **Docker API Linked** in Diagnostics — must be > 0.",
        0,
        y,
    )
)
y += 3

# --- Overview row ---
panels.append(row_panel(10, "Overview", y))
y += 1

status_thresholds = [
    {"color": "red", "value": None},
    {"color": "green", "value": 1},
]
panels.append(
    stat_panel(
        11,
        "Host Status",
        f'up{{{NODE}}}',
        "none",
        0,
        y,
        thresholds=status_thresholds,
        desc="1 = node-exporter reachable",
    )
)
panels.append(
    stat_panel(
        12,
        "CPU Usage",
        f'100 - (avg(rate(node_cpu_seconds_total{{{NODE},mode="idle"}}[5m])) * 100)',
        "percent",
        4,
        y,
    )
)
panels.append(
    stat_panel(
        13,
        "Memory Usage",
        f"(1 - (node_memory_MemAvailable_bytes{{{NODE}}} / node_memory_MemTotal_bytes{{{NODE}}})) * 100",
        "percent",
        8,
        y,
    )
)
panels.append(
    stat_panel(
        14,
        "Disk Usage (/)",
        f'100 - ((node_filesystem_avail_bytes{{{NODE},mountpoint="/",fstype!="rootfs"}} / node_filesystem_size_bytes{{{NODE},mountpoint="/",fstype!="rootfs"}}) * 100)',
        "percent",
        12,
        y,
    )
)
panels.append(
    stat_panel(
        15,
        "Running Containers",
        running_containers_expr(),
        "none",
        16,
        y,
        thresholds=[
            {"color": "blue", "value": None},
        ],
        desc="Running Docker containers only (excludes systemd cgroups)",
    )
)
panels.append(
    stat_panel(
        16,
        "Load (1m)",
        f'node_load1{{{NODE}}}',
        "none",
        20,
        y,
        thresholds=[
            {"color": "green", "value": None},
            {"color": "yellow", "value": 2},
            {"color": "red", "value": 4},
        ],
    )
)
y += 4

# --- Host performance ---
panels.append(row_panel(20, "Host Performance", y))
y += 1

panels.append(
    timeseries_panel(
        21,
        "CPU Usage Breakdown",
        [
            {
                "expr": f'100 - (avg by (mode) (rate(node_cpu_seconds_total{{{NODE},mode="idle"}}[5m])) * 100)',
                "legendFormat": "used",
                "refId": "A",
            },
            {
                "expr": f'avg(rate(node_cpu_seconds_total{{{NODE},mode="system"}}[5m])) * 100',
                "legendFormat": "system",
                "refId": "B",
            },
            {
                "expr": f'avg(rate(node_cpu_seconds_total{{{NODE},mode="user"}}[5m])) * 100',
                "legendFormat": "user",
                "refId": "C",
            },
            {
                "expr": f'avg(rate(node_cpu_seconds_total{{{NODE},mode="iowait"}}[5m])) * 100',
                "legendFormat": "iowait",
                "refId": "D",
            },
        ],
        0,
        y,
        w=12,
        unit="percent",
    )
)
panels.append(
    timeseries_panel(
        22,
        "Memory",
        [
            {
                "expr": f'node_memory_MemTotal_bytes{{{NODE}}} - node_memory_MemAvailable_bytes{{{NODE}}}',
                "legendFormat": "used",
                "refId": "A",
            },
            {
                "expr": f'node_memory_Cached_bytes{{{NODE}}}',
                "legendFormat": "cached",
                "refId": "B",
            },
            {
                "expr": f'node_memory_Buffers_bytes{{{NODE}}}',
                "legendFormat": "buffers",
                "refId": "C",
            },
        ],
        12,
        y,
        w=12,
        unit="bytes",
    )
)
y += 8

panels.append(
    timeseries_panel(
        23,
        "Disk I/O",
        [
            {
                "expr": f'rate(node_disk_read_bytes_total{{{NODE}}}[5m])',
                "legendFormat": "read {{device}}",
                "refId": "A",
            },
            {
                "expr": f'rate(node_disk_written_bytes_total{{{NODE}}}[5m])',
                "legendFormat": "write {{device}}",
                "refId": "B",
            },
        ],
        0,
        y,
        w=12,
        unit="Bps",
    )
)
panels.append(
    timeseries_panel(
        24,
        "Network I/O",
        [
            {
                "expr": f'rate(node_network_receive_bytes_total{{{NODE},device!~"lo|docker.*|veth.*|br.*"}}[5m])',
                "legendFormat": "rx {{device}}",
                "refId": "A",
            },
            {
                "expr": f'rate(node_network_transmit_bytes_total{{{NODE},device!~"lo|docker.*|veth.*|br.*"}}[5m])',
                "legendFormat": "tx {{device}}",
                "refId": "B",
            },
        ],
        12,
        y,
        w=12,
        unit="Bps",
    )
)
y += 8

# --- Containers ---
panels.append(row_panel(30, "Docker Containers", y))
y += 1

panels.append(
    {
        "id": 31,
        "type": "table",
        "title": "Container Overview",
        "description": "Live snapshot of all running containers on the selected server.",
        "gridPos": {"h": 9, "w": 24, "x": 0, "y": y},
        "datasource": {"type": "prometheus", "uid": "${datasource}"},
        "targets": [
            {
                "expr": container_cpu_rate(),
                "refId": "CPU",
                "format": "table",
                "instant": True,
            },
            {
                "expr": f'{CONTAINER_MEM}{{{CADVISOR}, {CONTAINER_FILTER}}}',
                "refId": "MEM",
                "format": "table",
                "instant": True,
            },
            {
                "expr": f'rate({CONTAINER_NET_RX}{{{CADVISOR}, {CONTAINER_FILTER}}}[5m])',
                "refId": "NET_RX",
                "format": "table",
                "instant": True,
            },
            {
                "expr": f'rate({CONTAINER_NET_TX}{{{CADVISOR}, {CONTAINER_FILTER}}}[5m])',
                "refId": "NET_TX",
                "format": "table",
                "instant": True,
            },
        ],
        "fieldConfig": {
            "defaults": {},
            "overrides": [
                {
                    "matcher": {"id": "byName", "options": "Value #MEM"},
                    "properties": [{"id": "unit", "value": "bytes"}],
                },
                {
                    "matcher": {"id": "byName", "options": "Value #CPU"},
                    "properties": [{"id": "unit", "value": "percent"}, {"id": "decimals", "value": 2}],
                },
                {
                    "matcher": {"id": "byName", "options": "Value #NET RX"},
                    "properties": [{"id": "unit", "value": "Bps"}],
                },
                {
                    "matcher": {"id": "byName", "options": "Value #NET TX"},
                    "properties": [{"id": "unit", "value": "Bps"}],
                },
            ],
        },
        "options": {"showHeader": True, "sortBy": [{"displayName": "Value #CPU", "desc": True}]},
        "transformations": [
            {"id": "seriesToColumns", "options": {"byField": "image"}},
            {
                "id": "organize",
                "options": {
                    "excludeByName": {
                        "Time": True,
                        "Time 1": True,
                        "Time 2": True,
                        "Time 3": True,
                        "Time 4": True,
                        "__name__": True,
                        "id": True,
                        "instance": True,
                        "job": True,
                        "name": True,
                        "container_label_com_docker_compose_project": True,
                        "container_label_com_docker_compose_service": True,
                        "container_label_com_docker_compose_version": True,
                    },
                    "renameByName": {
                        "image": "Container Image",
                        "Value #CPU": "CPU %",
                        "Value #MEM": "Memory",
                        "Value #NET RX": "Net RX",
                        "Value #NET TX": "Net TX",
                    },
                },
            },
        ],
    }
)
y += 9

panels.append(
    timeseries_panel(
        32,
        "Container CPU Usage",
        [
            {
                "expr": container_cpu_rate(),
                "legendFormat": "{{image}}",
                "refId": "A",
            }
        ],
        0,
        y,
        w=12,
        unit="percent",
        desc="Docker containers only — legend shows image name",
    )
)
panels.append(
    timeseries_panel(
        33,
        "Container Memory Usage",
        [
            {
                "expr": f'{CONTAINER_MEM}{{{CADVISOR}, {CONTAINER_FILTER}}}',
                "legendFormat": "{{image}}",
                "refId": "A",
            }
        ],
        12,
        y,
        w=12,
        unit="bytes",
    )
)
y += 8

# --- SUNPOR Services ---
panels.append(row_panel(40, "SUNPOR Application Services", y))
y += 1

sunpor_services = [
    ("sunpor-backend", "Backend API :8000"),
    ("sunpor-timescaledb", "TimescaleDB :5432"),
    ("sunpor-mqtt", "MQTT Broker :1883"),
    ("sunpor-frontend", "Frontend :3000"),
    ("mqtt-subscriber", "MQTT Subscriber"),
    ("node-exporter", "Node Exporter"),
    ("cadvisor", "cAdvisor"),
]

for i, (svc_name, svc_label) in enumerate(sunpor_services):
    col = (i % 4) * 6
    row_offset = (i // 4) * 6
    panels.append(
        {
            "id": 50 + i,
            "type": "stat",
            "title": svc_label,
            "gridPos": {"h": 6, "w": 6, "x": col, "y": y + row_offset},
            "datasource": {"type": "prometheus", "uid": "${datasource}"},
            "targets": [
                {
                    "expr": svc_running_expr(svc_name),
                    "refId": "A",
                }
            ],
            "fieldConfig": {
                "defaults": {
                    "mappings": [
                        {"type": "value", "options": {"0": {"text": "NOT RUNNING", "color": "red"}}},
                        {"type": "value", "options": {"1": {"text": "RUNNING", "color": "green"}}},
                    ],
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "red", "value": None},
                            {"color": "green", "value": 1},
                        ],
                    },
                    "color": {"mode": "thresholds"},
                },
                "overrides": [],
            },
            "options": {
                "reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                "textMode": "value",
                "colorMode": "background",
                "graphMode": "none",
                "justifyMode": "center",
            },
        }
    )

y += 12

# --- Diagnostics ---
panels.append(row_panel(55, "Diagnostics (cAdvisor)", y))
y += 1
panels.append(
    stat_panel(
        56,
        "cAdvisor Scrape Status",
        f'up{{{CADVISOR}}}',
        "none",
        0,
        y,
        w=6,
        thresholds=[
            {"color": "red", "value": None},
            {"color": "green", "value": 1},
        ],
        desc="1 = Prometheus can reach cAdvisor on :8080",
    )
)
panels.append(
    stat_panel(
        57,
        "Container Metric Series (Docker)",
        running_containers_expr(),
        "none",
        6,
        y,
        w=6,
        thresholds=[
            {"color": "red", "value": None},
            {"color": "yellow", "value": 1},
            {"color": "green", "value": 3},
        ],
        desc="Should match docker ps count (~6 on edge-s01)",
    )
)
panels.append(
    stat_panel(
        58,
        "Node Exporter Scrape Status",
        f'up{{{NODE}}}',
        "none",
        12,
        y,
        w=6,
        thresholds=[
            {"color": "red", "value": None},
            {"color": "green", "value": 1},
        ],
    )
)
panels.append(
    stat_panel(
        59,
        "Docker API Linked",
        docker_linked_expr(),
        "none",
        18,
        y,
        w=6,
        thresholds=[
            {"color": "red", "value": None},
            {"color": "green", "value": 1},
        ],
        desc="0 = cAdvisor cannot see Docker (mount docker.sock). Service panels need this > 0.",
    )
)
y += 4

# --- Gauges row ---
panels.append(row_panel(60, "Resource Gauges", y))
y += 1
for i, (title, expr) in enumerate(
    [
        ("CPU", f'100 - (avg(rate(node_cpu_seconds_total{{{NODE},mode="idle"}}[5m])) * 100)'),
        ("Memory", f"(1 - (node_memory_MemAvailable_bytes{{{NODE}}} / node_memory_MemTotal_bytes{{{NODE}}})) * 100"),
        ("Disk /", f'100 - ((node_filesystem_avail_bytes{{{NODE},mountpoint="/",fstype!="rootfs"}} / node_filesystem_size_bytes{{{NODE},mountpoint="/",fstype!="rootfs"}}) * 100)'),
        (
            "Swap",
            f"(1 - (node_memory_SwapFree_bytes{{{NODE}}} / (node_memory_SwapTotal_bytes{{{NODE}}} > 0))) * 100",
        ),
    ]
):
    panels.append(gauge_panel(61 + i, title, expr, i * 6, y))

dashboard = {
    "annotations": {
        "list": [
            {
                "builtIn": 1,
                "datasource": {"type": "grafana", "uid": "-- Grafana --"},
                "enable": True,
                "hide": True,
                "iconColor": "rgba(0, 211, 255, 1)",
                "name": "Annotations & Alerts",
                "type": "dashboard",
            }
        ]
    },
    "editable": True,
    "fiscalYearStartMonth": 0,
    "graphTooltip": 1,
    "id": None,
    "links": [],
    "liveNow": False,
    "panels": panels,
    "refresh": "30s",
    "schemaVersion": 39,
    "tags": ["sunpor", "edge", "production", "docker"],
    "templating": {
        "list": [
            {
                "current": {},
                "hide": 0,
                "includeAll": False,
                "label": "Prometheus",
                "name": "datasource",
                "options": [],
                "query": "prometheus",
                "refresh": 1,
                "regex": "",
                "type": "datasource",
            },
            {
                "current": {"selected": True, "text": "edge-s01", "value": "edge-s01"},
                "datasource": {"type": "prometheus", "uid": "${datasource}"},
                "definition": 'label_values(up{job=~"edge-.*"}, job)',
                "hide": 0,
                "includeAll": False,
                "label": "Server",
                "multi": False,
                "name": "server",
                "options": [],
                "query": {
                    "query": 'label_values(up{job=~"edge-.*"}, job)',
                    "refId": "PrometheusVariableQuery",
                },
                "refresh": 2,
                "regex": "",
                "sort": 1,
                "type": "query",
            },
            {
                "current": {"selected": True, "text": "All", "value": "$__all"},
                "datasource": {"type": "prometheus", "uid": "${datasource}"},
                "definition": f'label_values({CONTAINER_EXISTS}{{{CADVISOR}, {DOCKER_LABELLED}}}, name)',
                "hide": 0,
                "includeAll": True,
                "label": "Container",
                "multi": True,
                "name": "container",
                "options": [],
                "query": {
                    "query": f'label_values({CONTAINER_EXISTS}{{{CADVISOR}, {DOCKER_LABELLED}}}, name)',
                    "refId": "PrometheusVariableQuery",
                },
                "refresh": 2,
                "regex": "",
                "sort": 1,
                "type": "query",
            },
        ]
    },
    "time": {"from": "now-6h", "to": "now"},
    "timepicker": {},
    "timezone": "browser",
    "title": "SUNPOR Edge Infrastructure",
    "uid": "sunpor-edge-overview",
    "version": 4,
    "weekStart": "",
}

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps(dashboard, indent=2), encoding="utf-8")
print(f"Generated {OUTPUT}")
