# Essential Nginx Commands

Every Nginx command you need for daily operations, process management, and signal handling.

---

# Starting and Stopping Nginx

## Start Nginx

```bash
# Start using systemd (recommended on modern Linux)
sudo systemctl start nginx

# Start directly (uses default config at /etc/nginx/nginx.conf)
sudo nginx

# Start with a custom config file
sudo nginx -c /path/to/custom/nginx.conf

# Start with a custom prefix path (changes the base directory for all relative paths)
sudo nginx -p /opt/nginx/
```

## Stop Nginx

```bash
# Graceful stop — finishes processing current requests, then shuts down
sudo nginx -s quit

# Immediate stop — terminates all connections instantly
sudo nginx -s stop

# Using systemd
sudo systemctl stop nginx
```

**Production Rule**: Always use `nginx -s quit` for graceful shutdown. `nginx -s stop` sends SIGTERM and kills active connections — users will see broken responses.

---

# Reloading Configuration (Zero Downtime)

```bash
# Test configuration FIRST (always!)
sudo nginx -t

# If test passes, reload
sudo nginx -s reload
```

## What Happens During Reload

```text
1. Master process reads new configuration
2. Master validates the new configuration
3. Master spawns NEW worker processes with new config
4. Master signals OLD workers to stop accepting new connections
5. OLD workers finish processing current requests
6. OLD workers shut down gracefully
7. Only NEW workers remain — serving with new config

   At NO point are requests dropped. This is zero-downtime.

Timeline:
  ──────────────────────────────────────────────►
  │ Old workers (serving)  │ Old workers (draining) │
  │                        │ New workers (serving)    │
  │                        │                          │ Old workers exit
  reload signal            │                          │
                           new config active          done
```

**Critical**: NEVER reload without testing first. A bad config will be rejected by `nginx -s reload`, but some edge cases can cause the master process to fail. Always run `nginx -t` before `nginx -s reload`.

---

# Testing Configuration

```bash
# Test the default config file
sudo nginx -t
# Output on success:
#   nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
#   nginx: configuration file /etc/nginx/nginx.conf test is successful

# Test a specific config file
sudo nginx -t -c /etc/nginx/nginx-staging.conf

# Dump the full resolved configuration (includes all included files, resolved variables)
sudo nginx -T

# Dump config to a file for review or diff
sudo nginx -T > /tmp/nginx-full-config.txt
```

**`nginx -t` vs `nginx -T`**:
- `-t` (lowercase): Tests syntax and exits. Outputs only pass/fail.
- `-T` (uppercase): Tests syntax AND prints the entire resolved configuration to stdout. Invaluable for debugging include chains.

---

# Version and Build Information

```bash
# Show version number only
nginx -v
# Output: nginx version: nginx/1.24.0

# Show version, compiler flags, configure arguments, and built-in modules
nginx -V
# Output includes:
#   --with-http_ssl_module
#   --with-http_v2_module
#   --with-http_realip_module
#   --with-http_stub_status_module
#   --with-http_gzip_static_module
#   ...
```

**Use `nginx -V` to check**:
- Which modules are compiled in (e.g., is `http_v2_module` available?)
- The OpenSSL version linked (affects TLS 1.3 support)
- The configure prefix path (where Nginx looks for configs by default)

---

# Process Management

## Viewing Nginx Processes

```bash
# Show master and worker processes
ps aux | grep nginx

# Output:
# root     1234  0.0  0.1  nginx: master process /usr/sbin/nginx
# www-data 1235  0.0  0.2  nginx: worker process
# www-data 1236  0.0  0.2  nginx: worker process
# www-data 1237  0.0  0.2  nginx: worker process
# www-data 1238  0.0  0.2  nginx: worker process

# Count worker processes
ps aux | grep "nginx: worker" | grep -v grep | wc -l

# Show the master process PID
cat /run/nginx.pid
# or
cat /var/run/nginx.pid
```

## Signal Handling

Nginx uses Unix signals for process management. The `-s` flag is a convenience wrapper:

| Command | Signal | Behavior |
|---------|--------|----------|
| `nginx -s stop` | `SIGTERM` | Immediate shutdown (kills connections) |
| `nginx -s quit` | `SIGQUIT` | Graceful shutdown (drains connections) |
| `nginx -s reload` | `SIGHUP` | Hot reload configuration |
| `nginx -s reopen` | `SIGUSR1` | Reopen log files (for log rotation) |

You can also send signals directly:

```bash
# Send reload signal directly to master process
sudo kill -HUP $(cat /run/nginx.pid)

# Send log reopen signal
sudo kill -USR1 $(cat /run/nginx.pid)

# Graceful shutdown
sudo kill -QUIT $(cat /run/nginx.pid)
```

---

# Log Rotation with `reopen`

When log files are rotated (e.g., by `logrotate`), Nginx continues writing to the old file descriptor. You must tell Nginx to reopen its log files:

```bash
# Rotate logs
sudo mv /var/log/nginx/access.log /var/log/nginx/access.log.1
sudo mv /var/log/nginx/error.log /var/log/nginx/error.log.1

# Tell Nginx to open new log files
sudo nginx -s reopen

# Compress old logs
sudo gzip /var/log/nginx/access.log.1
```

**logrotate configuration** (`/etc/logrotate.d/nginx`):

```text
/var/log/nginx/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        [ -f /run/nginx.pid ] && kill -USR1 $(cat /run/nginx.pid)
    endscript
}
```

---

# Systemd Management

```bash
# Start, stop, restart, reload
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx    # Full restart (drops connections!)
sudo systemctl reload nginx     # Graceful reload (zero downtime)

# Enable auto-start on boot
sudo systemctl enable nginx

# Disable auto-start
sudo systemctl disable nginx

# Check status
sudo systemctl status nginx

# View recent logs
sudo journalctl -u nginx --since "5 minutes ago"
sudo journalctl -u nginx -f    # Follow logs in real time
```

**`restart` vs `reload`**:
- `restart` = stop + start (drops all connections, brief downtime)
- `reload` = hot reload (zero downtime, graceful worker drain)

Always prefer `reload` in production. Use `restart` only when major changes require it (e.g., changing the listening port on the master process, or upgrading the Nginx binary).

---

# Common Mistakes

- Running `nginx -s reload` without `nginx -t` first. If the config has errors, the reload fails and workers continue with the old config — but edge cases exist.
- Using `systemctl restart` instead of `systemctl reload` in production. Restart drops all active connections.
- Forgetting `nginx -s reopen` after log rotation — Nginx keeps writing to the deleted file descriptor, and your new log file stays empty.
- Running Nginx commands without `sudo` — the master process runs as root and requires root privileges for management signals.
- Not checking `nginx -V` to confirm required modules are compiled in before adding config directives that depend on them.

---

# Key Takeaways

- Always test before reload: `nginx -t && nginx -s reload`.
- Reload is zero-downtime (graceful worker drain). Restart drops connections.
- `nginx -T` dumps the full resolved configuration — essential for debugging.
- Use `nginx -s reopen` after log rotation to avoid writing to stale file descriptors.
- `nginx -V` shows compiled modules — check this before enabling features like HTTP/2 or stub_status.
- Prefer `systemctl reload nginx` over `systemctl restart nginx` in production.

---
