# Nginx CLI Operations

A production-focused guide to Nginx command-line operations covering daily management, configuration workflows, log analysis, performance debugging, and SSL certificate management.

---

# Topics Covered

| # | Topic | Key Concepts |
|---|-------|-------------|
| 01 | [Essential Commands](./01-%20Essential%20Commands.md) | Start, stop, reload, test, version, process management, signal handling |
| 02 | [Configuration Management](./02-%20Configuration%20Management.md) | Config testing, hot reload, include patterns, diff workflows, rollback |
| 03 | [Log Analysis](./03-%20Log%20Analysis.md) | Access/error log parsing, real-time monitoring, one-liners for traffic analysis |
| 04 | [Performance Debugging](./04-%20Performance%20Debugging.md) | Connection analysis, worker tuning, stub_status, load testing with ab/wrk |
| 05 | [SSL Certificate Management](./05-%20SSL%20Certificate%20Management.md) | Let's Encrypt/certbot, certificate inspection, renewal, OCSP stapling |

---

# Quick Reference

```text
# The 5 commands you'll use every day:

nginx -t                    # Test configuration (ALWAYS before reload)
nginx -s reload             # Hot reload (zero downtime)
nginx -T                    # Dump full resolved config
tail -f /var/log/nginx/error.log   # Watch errors in real time
curl -I http://localhost    # Quick health check
```

---

# Navigation

| Direction | Link |
|-----------|------|
| ⬆️ Parent | [Nginx Module](../README.md) |
| ⬅️ Related | [Concepts](../concepts/) |
| ➡️ Related | [Troubleshooting](../troubleshooting/) |

---

*Part of the [Backend Engineering Playbook](../../) — Aranya Majumdar*
