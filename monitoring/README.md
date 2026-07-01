# SUNPOR Monitoring (Prometheus + Grafana)

Production-ready monitoring for SUNPOR edge nodes with a **server switcher** dashboard.

## Architecture

```
monitoring-server
├── Prometheus  (:9090)  — scrapes all edge nodes
└── Grafana     (:3000)  — SUNPOR Edge Infrastructure dashboard

edge-s01 / edge-s02 (each)
├── node-exporter  (:9100)  — host metrics
├── cAdvisor       (:8080)  — container metrics
└── SUNPOR stack   (backend, DB, MQTT, etc.)
```

## Quick deploy on monitoring-server

### 1. Update Prometheus config

Your current config (`prometheus.legacy.yml`) works with the dashboard as-is.

For **new servers and multi-platform** support, migrate to `prometheus/prometheus.yml` (adds `server` and `platform` labels):

```bash
# On monitoring-server
cp monitoring/prometheus/prometheus.yml ~/monitoring/prometheus/prometheus.yml
docker compose restart prometheus   # or: systemctl restart prometheus
```

**Add a new edge server** — append targets in both `node-exporter` and `cadvisor` blocks:

```yaml
      - targets:
          - 100.x.x.x:9100
        labels:
          server: edge-s03
          platform: sunpor
          role: edge
```

After migrating to the new config, update the Grafana **Server** variable query to:

```promql
label_values(up{server!=""}, server)
```

### 2. Import Grafana dashboard

**Option A — UI import (fastest)**

1. Open Grafana → **Dashboards** → **New** → **Import**
2. Upload `monitoring/grafana/dashboards/sunpor-edge-overview.json`
3. Select your Prometheus datasource
4. Click **Import**

**Option B — Provisioning (persistent)**

Copy files on the monitoring server:

```bash
sudo cp monitoring/grafana/dashboards/sunpor-edge-overview.json \
  /etc/grafana/provisioning/dashboards/

sudo cp monitoring/grafana/provisioning/dashboards/dashboards.yml \
  /etc/grafana/provisioning/dashboards/

sudo cp monitoring/grafana/provisioning/datasources/datasources.yml \
  /etc/grafana/provisioning/datasources/

sudo systemctl restart grafana-server
```

Adjust the Prometheus URL in `datasources.yml` if needed (e.g. `http://prometheus:9090` in Docker).

### 3. Regenerate dashboard (after edits)

```bash
python monitoring/scripts/generate_dashboard.py
```

## Dashboard features

| Section | What you see |
|--------|----------------|
| **Server** dropdown | Switch between `edge-s01`, `edge-s02` (auto-discovers new jobs) |
| **Container** filter | Optional multi-select filter (for future drill-down) |
| **Overview** | Host status, CPU, memory, disk, container count, load |
| **Host Performance** | CPU breakdown, memory, disk I/O, network I/O |
| **Docker Containers** | Live table + CPU/memory time series per container |
| **SUNPOR Services** | RUNNING / NOT RUNNING cards per service |
| **Resource Gauges** | CPU, memory, disk, swap at a glance |

Auto-refresh: **30 seconds**.

## Expected containers per server

| Service | edge-s01 | edge-s02 |
|---------|:--------:|:--------:|
| sunpor-backend | ✓ | ✓ |
| sunpor-timescaledb | ✓ | ✓ |
| sunpor-mqtt | ✓ | — |
| sunpor-frontend | — | ✓ |
| mqtt-subscriber | ✓ | ✓ |
| node-exporter | ✓ | ✓ |
| cadvisor | ✓ | ✓ |

Services not deployed on a server show **NOT RUNNING** (expected).

## Files

```
monitoring/
├── cadvisor/
│   └── docker-compose.yml      # FIX: mounts docker.sock (required!)
├── prometheus/
│   ├── prometheus.yml          # Recommended (labeled, scalable)
│   └── prometheus.legacy.yml   # Your current setup
├── grafana/
│   ├── dashboards/
│   │   └── sunpor-edge-overview.json
│   └── provisioning/
│       ├── dashboards/dashboards.yml
│       └── datasources/datasources.yml
├── scripts/
│   └── generate_dashboard.py
└── README.md
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Server dropdown empty | Check Prometheus targets: `http://<monitor>:9090/targets` |
| Host metrics OK but **containers show No data** | See **cAdvisor fix checklist** below |
| All services show **NOT RUNNING** | Same as above — cAdvisor metrics not in Prometheus |
| NOT RUNNING for one service only | Expected if that container is not on that server (e.g. frontend on edge-s01) |

### Root cause: cAdvisor not linked to Docker (most common)

If host metrics work but **all container panels show No data**, check your metrics:

```bash
curl -s http://100.75.166.124:8080/metrics | grep cadvisor_version_info
```

If `dockerVersion=""` → **cAdvisor cannot see Docker**. Metrics only export systemd cgroups (`/system.slice/...`) without `name` or `image` labels. The Grafana dashboard cannot show per-container data until this is fixed.

**Fix on each edge node:**

```bash
# Stop broken cAdvisor
docker stop cadvisor && docker rm cadvisor

# Deploy fixed version (mounts docker.sock)
cd monitoring/cadvisor
docker compose up -d

# Verify — must show Docker version, NOT empty:
curl -s http://localhost:8080/metrics | grep cadvisor_version_info

# Must return lines with name= and image= labels:
curl -s http://localhost:8080/metrics | grep 'name="/sunpor' | head -3
```

After fix, re-import dashboard v4. **Docker API Linked** panel in Diagnostics should show **6** (or your container count).

### Why "Running Containers" showed 1 (not 6)?

Ubuntu 24.04 uses **cgroup v2**. cAdvisor exports:
- **42 systemd series** (`/system.slice`, `/user.slice`, …) — noise
- **6 Docker series** (`/system.slice/docker-<id>.scope`) — actual containers

The old query counted by `name` label (mostly empty on cgroup v2) → result was **1**.

Dashboard v3 filters Docker cgroups only:
```promql
id=~"/docker/.+|/system.slice/docker-[a-f0-9]+\\.scope"
```

Verify in Prometheus:
```promql
count(count by (id) (container_tasks_state{job="edge-s01", instance=~".*:8080", state="running", id=~"/system.slice/docker-.+\\.scope"} > 0))
```
Expected: **6** on edge-s01.

### cAdvisor fix checklist

**1. Check Prometheus targets** (on monitoring-server):

Open `http://<monitoring-server>:9090/targets` and confirm both targets per server are **UP**:
- `100.75.166.124:9100` (node-exporter)
- `100.75.166.124:8080` (cAdvisor) ← often this one fails

**2. Test cAdvisor metrics directly** (from monitoring-server):

```bash
curl -s http://100.75.166.124:8080/metrics | head -20
curl -s http://100.75.166.124:8080/metrics | grep container_start_time_seconds | head -5
```

If this fails, cAdvisor is not reachable from the monitoring server (firewall / Tailscale).

**3. Query in Prometheus UI:**

```promql
container_start_time_seconds{job="edge-s01", instance=~".*:8080", id!="/"}
```

If empty → Prometheus is not scraping cAdvisor. Add `scrape_timeout: 30s` to your job (see `prometheus.legacy.yml`).

**4. Re-import dashboard** after pulling latest `sunpor-edge-overview.json` (v2 fixes):
- Uses `container_start_time_seconds` instead of `container_last_seen`
- Matches container names with leading slash (`/sunpor-backend`)
- Adds **Diagnostics (cAdvisor)** row at bottom

**5. cAdvisor container on edge node** must mount Docker socket:

```yaml
volumes:
  - /:/rootfs:ro
  - /var/run:/var/run:ro
  - /sys:/sys:ro
  - /var/lib/docker/:/var/lib/docker:ro
  - /var/run/docker.sock:/var/run/docker.sock:ro
```
