# Troubleshooting: Connection Refused

## What "Connection Refused" Actually Means

The network layer let the packet through and reached the instance — but the operating system on that specific port responded with an explicit rejection, rather than the request timing out or being silently dropped. This is a meaningfully different signal from a timeout (see that file): it tells you the network path is fine, and the problem is on the instance itself.

## Common Causes

**The application isn't running at all**

The process (Gunicorn, Node, nginx, whatever's expected to be listening) has crashed, failed to start, or was never started in the first place.

```bash
# Check if the process is actually running
ps aux | grep <process-name>

# Check if anything is listening on the expected port
sudo netstat -tlnp | grep <port>
# or
sudo ss -tlnp | grep <port>
```

**The application is bound to the wrong interface**

A service bound to `127.0.0.1` (localhost only) accepts connections only from *within* the instance itself — external traffic reaching that port gets refused because nothing external-facing is actually listening. The fix is binding to `0.0.0.0` (all interfaces) instead, assuming external access is actually intended.

```text
Bound to 127.0.0.1:8000  → only reachable from inside the instance
Bound to 0.0.0.0:8000    → reachable from any interface, including external
```

**The application crashed after a health check passed**

A process that started successfully but has since crashed (an unhandled exception, an out-of-memory kill) leaves nothing listening on the port anymore, even though the instance itself is still running and reachable.

## A Practical Debugging Sequence

```text
1. Confirm the instance itself is reachable (ping, or SSH if that port works)
2. SSH in and check whether the expected process is actually running
3. Check what's listening on the specific port, and on which interface
4. Check application logs for a crash, and system logs (journalctl, dmesg)
   for an OOM kill or similar
5. If bound to 127.0.0.1 but external access is needed, fix the bind address
   and restart
```

## Senior-Level Considerations

- Connection Refused ruling out the network layer (Security Groups, NACLs, routing) is genuinely useful diagnostic information — it means time is better spent on the application/process layer rather than re-checking security group rules that are, by definition, already allowing the traffic through
- A process manager (systemd, supervisord, or a container orchestrator's own restart policy) that automatically restarts a crashed process turns "the app is down until someone notices and SSHes in" into "briefly down, then self-healed" — worth having in place before this becomes a 3am page rather than after
