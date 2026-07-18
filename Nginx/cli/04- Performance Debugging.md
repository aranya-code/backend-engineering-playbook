# Performance Debugging

CLI techniques for diagnosing Nginx performance issues, analyzing connections, tuning workers, and load testing.

---

# stub_status — Live Connection Metrics

Enable the stub_status module to expose real-time connection statistics:

```nginx
# Add to your Nginx config (restrict to internal/monitoring IPs only)
server {
    listen 8080;
    location /nginx_status {
        stub_status on;
        allow 127.0.0.1;      # Localhost
        allow 10.0.0.0/8;     # Internal network
        deny all;              # Block everyone else
    }
}
```

```bash
# Query the status endpoint
curl http://localhost:8080/nginx_status

# Output:
# Active connections: 42
# server accepts handled requests
#  1234567 1234567 8901234
# Reading: 3 Writing: 12 Waiting: 27
```

## Understanding the Output

```text
Active connections: 42        ← Total open connections right now
                                (Reading + Writing + Waiting)

server accepts handled requests
 1234567 1234567 8901234
    │       │       │
    │       │       └── Total requests processed (cumulative)
    │       └── Total connections handled (should equal accepts)
    └── Total connections accepted (cumulative)

If "handled" < "accepts", connections were dropped (worker_connections too low!)

Reading: 3                    ← Reading request headers from client
Writing: 12                   ← Sending response to client
Waiting: 27                   ← Keep-alive connections waiting for next request
                                (idle but open — this is normal and expected)
```

## Monitoring Script

```bash
# Request rate per second (run twice, 1 second apart)
REQ1=$(curl -s http://localhost:8080/nginx_status | awk 'NR==3{print $3}')
sleep 1
REQ2=$(curl -s http://localhost:8080/nginx_status | awk 'NR==3{print $3}')
echo "Requests/sec: $((REQ2 - REQ1))"
```

---

# Connection Analysis

## View Active Connections

```bash
# Count connections to Nginx by state
ss -tn state established '( sport = :80 or sport = :443 )' | wc -l

# Connections by state (ESTABLISHED, TIME_WAIT, CLOSE_WAIT)
ss -tan '( sport = :80 or sport = :443 )' | awk '{print $1}' | sort | uniq -c | sort -rn

# Output:
#   423 ESTAB
#   156 TIME-WAIT
#    23 CLOSE-WAIT     ← If high, backend is not closing connections properly
#     5 SYN-RECV

# Connections per client IP
ss -tn state established '( sport = :80 or sport = :443 )' | \
    awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -rn | head -10
```

## Diagnosing Connection Issues

```text
High TIME-WAIT:
  → Normal after many short-lived connections
  → Tune kernel: net.ipv4.tcp_tw_reuse = 1

High CLOSE-WAIT:
  → Backend is not closing connections properly
  → Check upstream application for connection leaks

High SYN-RECV:
  → Possible SYN flood attack
  → Enable SYN cookies: net.ipv4.tcp_syncookies = 1

"accepts" > "handled" in stub_status:
  → worker_connections is too low
  → Increase: worker_connections 4096;
```

---

# Worker Process Tuning

## Check Current Worker Configuration

```bash
# How many worker processes are running?
ps aux | grep "nginx: worker" | grep -v grep | wc -l

# How many CPU cores does the server have?
nproc
# or
grep -c ^processor /proc/cpuinfo

# What is worker_connections set to?
sudo nginx -T | grep worker_connections

# What is the current open file limit?
cat /proc/$(cat /run/nginx.pid)/limits | grep "Max open files"
```

## Optimal Worker Settings

```text
Rule of Thumb:

worker_processes = Number of CPU cores
worker_connections = 1024 to 4096 (depends on traffic)

Max concurrent connections = worker_processes × worker_connections

Example (4-core server):
  worker_processes 4;
  worker_connections 2048;
  Max connections = 4 × 2048 = 8,192 simultaneous connections

For reverse proxy (each client = 2 connections: client→nginx + nginx→backend):
  Effective max clients = worker_processes × worker_connections / 2
  = 4 × 2048 / 2 = 4,096 simultaneous clients
```

---

# File Descriptor Limits

```bash
# Check system-wide file descriptor limit
cat /proc/sys/fs/file-max

# Check current usage
cat /proc/sys/fs/file-nr
# Output: <allocated> <free> <max>
# Example: 3456 0 1048576

# Check per-process limit for Nginx worker
cat /proc/$(pgrep -f "nginx: worker" | head -1)/limits | grep "Max open files"

# Set in Nginx config:
worker_rlimit_nofile 65535;
# This should be >= worker_connections × 2

# Set in systemd override (if using systemd):
sudo systemctl edit nginx
# Add:
# [Service]
# LimitNOFILE=65535
```

**Common Issue**: If `worker_connections` is set to 4096 but the OS file descriptor limit is 1024, Nginx silently caps connections at 1024. Always verify the OS limit matches.

---

# Load Testing

## Apache Benchmark (ab)

```bash
# Install
sudo apt install apache2-utils    # Debian/Ubuntu
sudo yum install httpd-tools      # RHEL/CentOS

# Basic load test: 10,000 requests, 100 concurrent
ab -n 10000 -c 100 http://localhost/

# With keep-alive connections
ab -n 10000 -c 100 -k http://localhost/

# Key metrics in output:
#   Requests per second:    8234.56 [#/sec]
#   Time per request:       12.143 [ms]
#   Failed requests:        0
#   50%     10ms
#   95%     25ms
#   99%     48ms
```

## wrk (Modern Load Testing)

```bash
# Install
sudo apt install wrk

# 30-second test with 4 threads and 100 connections
wrk -t4 -c100 -d30s http://localhost/

# Output:
#   Requests/sec:  12345.67
#   Latency Avg:   8.12ms
#   Latency 99%:   42.31ms
#   Transfer/sec:  45.23MB
```

## Interpreting Results

```text
Metric              Healthy         Warning          Critical
─────────────────   ─────────────   ──────────────   ─────────────
Requests/sec        > 1000          100-1000         < 100
Avg Latency         < 50ms          50-200ms         > 200ms
99th Percentile     < 200ms         200-1000ms       > 1000ms
Failed Requests     0               < 1%             > 1%
```

---

# Kernel Tuning for High Traffic

```bash
# Check current kernel parameters
sysctl net.core.somaxconn                    # Max pending connections queue
sysctl net.ipv4.tcp_max_syn_backlog          # SYN queue size
sysctl net.ipv4.ip_local_port_range          # Ephemeral port range

# Recommended production tuning (/etc/sysctl.conf)
net.core.somaxconn = 65535                   # Default 128 — too low for production
net.core.netdev_max_backlog = 65535          # Network device input queue
net.ipv4.tcp_max_syn_backlog = 65535         # SYN queue
net.ipv4.ip_local_port_range = 1024 65535    # More ephemeral ports
net.ipv4.tcp_tw_reuse = 1                   # Reuse TIME_WAIT sockets
net.ipv4.tcp_fin_timeout = 15               # Reduce FIN_WAIT2 timeout
net.ipv4.tcp_keepalive_time = 300            # Keepalive probe interval
net.core.rmem_max = 16777216                 # Max receive buffer
net.core.wmem_max = 16777216                 # Max send buffer

# Apply without reboot
sudo sysctl -p
```

---

# Quick Diagnostic Checklist

```bash
# 1. Is Nginx running?
systemctl status nginx

# 2. Is config valid?
nginx -t

# 3. What's the current load?
curl -s http://localhost:8080/nginx_status

# 4. How many connections?
ss -tn state established '( sport = :80 or sport = :443 )' | wc -l

# 5. Are workers at capacity?
ps aux | grep "nginx: worker" | awk '{print $3, $4}'  # CPU% and MEM%

# 6. Is the upstream responding?
curl -w "Connect: %{time_connect}s\nTTFB: %{time_starttransfer}s\nTotal: %{time_total}s\n" \
     -o /dev/null -s http://localhost:8080/health

# 7. Any errors in the last 5 minutes?
sudo journalctl -u nginx --since "5 minutes ago" --no-pager

# 8. File descriptor usage
ls /proc/$(pgrep -f "nginx: worker" | head -1)/fd | wc -l
```

---

# Common Mistakes

- Not enabling `stub_status` — you're flying blind without real-time connection metrics.
- Setting `worker_connections` high but not increasing the OS file descriptor limit (`LimitNOFILE`).
- Load testing from the same machine as the Nginx server — results are meaningless due to resource contention.
- Ignoring `TIME_WAIT` sockets — on high-traffic servers, you can exhaust ephemeral ports. Enable `tcp_tw_reuse`.
- Using `ab` for serious benchmarks — `wrk` provides more accurate results with proper threading.

---

# Key Takeaways

- Enable `stub_status` on every Nginx instance. It's the first thing to check during incidents.
- `worker_processes` = CPU cores. `worker_connections` = 1024–4096. OS `nofile` limit must be ≥ 2× `worker_connections`.
- Use `ss` (not `netstat`) for connection analysis — it's faster and more accurate.
- Load test with `wrk` for realistic results. Focus on p99 latency, not just average.
- Tune kernel parameters (`somaxconn`, `tcp_tw_reuse`, `port_range`) for high-traffic servers.
- The quick diagnostic checklist should be your first 60 seconds during any Nginx incident.

---
