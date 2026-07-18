# Log Analysis

Production-ready CLI one-liners and techniques for analyzing Nginx access and error logs.

---

# Log File Locations

```text
Default locations:
  /var/log/nginx/access.log         # All incoming requests
  /var/log/nginx/error.log          # Errors, warnings, and debug messages

Docker:
  docker logs <container_name>      # stdout/stderr (default)
  docker exec <container> cat /var/log/nginx/access.log

Kubernetes:
  kubectl logs <pod> -c nginx       # Container logs
```

---

# Access Log Format

The default `combined` log format:

```text
$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"

Example:
203.0.113.42 - - [18/Jul/2026:10:30:15 +0000] "GET /api/users HTTP/1.1" 200 1234 "https://example.com" "Mozilla/5.0"
```

| Field | Position | Example | Meaning |
|-------|----------|---------|---------|
| `$remote_addr` | 1 | `203.0.113.42` | Client IP |
| `$remote_user` | 3 | `-` | Authenticated user (usually empty) |
| `$time_local` | 4 | `[18/Jul/2026:10:30:15 +0000]` | Request timestamp |
| `$request` | 6 | `"GET /api/users HTTP/1.1"` | Method, URI, protocol |
| `$status` | 7 | `200` | HTTP status code |
| `$body_bytes_sent` | 8 | `1234` | Response body size |
| `$http_referer` | 9 | `"https://example.com"` | Referring page |
| `$http_user_agent` | 10 | `"Mozilla/5.0..."` | Client browser/agent |

---

# Real-Time Log Monitoring

```bash
# Follow access log in real time
tail -f /var/log/nginx/access.log

# Follow error log in real time
tail -f /var/log/nginx/error.log

# Follow both simultaneously (split terminal or use multitail)
multitail /var/log/nginx/access.log /var/log/nginx/error.log

# Follow and filter for errors only (4xx and 5xx)
tail -f /var/log/nginx/access.log | grep --line-buffered -E '" [45][0-9]{2} '

# Follow and filter for a specific endpoint
tail -f /var/log/nginx/access.log | grep --line-buffered '/api/payments'

# Follow and filter for slow requests (using custom log format with $request_time)
tail -f /var/log/nginx/access.log | awk -F'"' '{if ($NF > 2.0) print $0}'
```

---

# Traffic Analysis One-Liners

## Top IPs by Request Count

```bash
# Top 20 client IPs
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -20

# Output:
#   15234 203.0.113.42
#    8921 198.51.100.23
#    4521 10.0.1.50
```

## Top Requested URLs

```bash
# Top 20 most requested URLs
awk '{print $7}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -20

# Exclude static assets
awk '{print $7}' /var/log/nginx/access.log | grep -v -E '\.(css|js|png|jpg|svg|ico|woff)' | sort | uniq -c | sort -rn | head -20
```

## Status Code Distribution

```bash
# Count by status code
awk '{print $9}' /var/log/nginx/access.log | sort | uniq -c | sort -rn

# Output:
#   45231 200
#    3421 304
#    1234 404
#     567 500
#     123 502

# Show only error codes (4xx and 5xx)
awk '$9 ~ /^[45]/' /var/log/nginx/access.log | awk '{print $9}' | sort | uniq -c | sort -rn
```

## Requests Per Second / Minute / Hour

```bash
# Requests per second (current traffic rate)
awk '{print $4}' /var/log/nginx/access.log | cut -d: -f1-3 | uniq -c | tail -10

# Requests per minute
awk '{print $4}' /var/log/nginx/access.log | cut -d: -f1-2 | sort | uniq -c | sort -rn | head -20

# Requests per hour
awk '{print $4}' /var/log/nginx/access.log | cut -d: -f1 | sort | uniq -c

# Total requests today
wc -l /var/log/nginx/access.log
```

## Bandwidth Usage

```bash
# Total bytes served
awk '{sum += $10} END {printf "%.2f GB\n", sum/1024/1024/1024}' /var/log/nginx/access.log

# Bandwidth per URL (top consumers)
awk '{urls[$7] += $10} END {for (u in urls) printf "%10.2f MB  %s\n", urls[u]/1024/1024, u}' \
    /var/log/nginx/access.log | sort -rn | head -20
```

---

# Error Log Analysis

## Error Log Severity Levels

```text
Level       Description                    Action Required
─────────   ──────────────────────────     ────────────────
emerg       System is unusable              Immediate
alert       Action must be taken            Immediate
crit        Critical conditions             Immediate
error       Error conditions                Investigate
warn        Warning conditions              Monitor
notice      Normal but significant          Informational
info        Informational messages          Debug only
debug       Debug-level messages            Development only
```

```bash
# Count errors by severity
grep -oP '\[(emerg|alert|crit|error|warn)\]' /var/log/nginx/error.log | sort | uniq -c | sort -rn

# Show only critical+ errors
grep -E '\[(emerg|alert|crit)\]' /var/log/nginx/error.log

# Find upstream connection failures (502 root cause)
grep 'upstream' /var/log/nginx/error.log | grep -i 'connect\|refuse\|timeout' | tail -20

# Find SSL errors
grep -i 'ssl' /var/log/nginx/error.log | tail -20

# Find permission denied errors
grep 'Permission denied' /var/log/nginx/error.log | tail -20
```

---

# Identifying Attacks and Anomalies

```bash
# Find potential brute force attacks (high request rate from single IP)
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -5
# If any IP has orders of magnitude more requests, investigate further

# Find bot traffic
grep -i 'bot\|crawler\|spider\|scraper' /var/log/nginx/access.log | awk '{print $1}' | sort | uniq -c | sort -rn

# Find requests with suspicious user agents (empty or curl/wget)
awk -F'"' '$6 == "-" || $6 ~ /curl|wget|python|scrapy/' /var/log/nginx/access.log | wc -l

# Find 404 enumeration attempts (path scanning)
awk '$9 == 404 {print $7}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -20

# Find requests to admin/sensitive paths
grep -E '/(admin|wp-admin|phpmyadmin|.env|.git|wp-login)' /var/log/nginx/access.log | tail -20
```

---

# Custom Log Format for Production

Add timing information for performance analysis:

```nginx
log_format detailed '$remote_addr - $remote_user [$time_local] '
                    '"$request" $status $body_bytes_sent '
                    '"$http_referer" "$http_user_agent" '
                    'rt=$request_time urt=$upstream_response_time '
                    'cs=$upstream_cache_status';
```

Then analyze response times:

```bash
# Average response time
grep -oP 'rt=\K[0-9.]+' /var/log/nginx/access.log | \
    awk '{sum += $1; count++} END {printf "%.3f seconds\n", sum/count}'

# Slowest requests (top 20)
grep -oP 'rt=\K[0-9.]+.*' /var/log/nginx/access.log | sort -rn | head -20

# Requests slower than 2 seconds
grep -P 'rt=(?:[2-9]\.|[0-9]{2,}\.)' /var/log/nginx/access.log | tail -20

# Cache hit ratio
grep -oP 'cs=\K\w+' /var/log/nginx/access.log | sort | uniq -c | sort -rn
# Output:
#   8234 HIT
#   1234 MISS
#    567 EXPIRED
#     89 BYPASS
```

---

# Common Mistakes

- Not using `--line-buffered` with `grep` on piped `tail -f` — output may be delayed without it.
- Analyzing large log files with `cat` + `grep` instead of `awk` — awk is 5–10x faster for field-based extraction.
- Not setting up a custom log format with `$request_time` — you can't analyze slow requests without it.
- Ignoring error log severity levels — not all errors are equal. Focus on `crit` and `emerg` first.
- Not rotating logs — an unrotated access log can grow to hundreds of GB and fill the disk.

---

# Key Takeaways

- `tail -f` with `grep --line-buffered` is the fastest way to monitor live traffic.
- `awk` is your primary tool for log analysis — learn the field positions by heart.
- Always add `$request_time` and `$upstream_response_time` to your log format for performance visibility.
- Status code distribution reveals the health of your application at a glance.
- Check error logs by severity — `emerg` and `crit` require immediate action.
- Rotate logs with `logrotate` + `nginx -s reopen` to prevent disk exhaustion.

---
