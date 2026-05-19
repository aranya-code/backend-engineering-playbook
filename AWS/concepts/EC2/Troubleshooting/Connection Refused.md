### Connection Refused
If it rejects the connection immediately, the network allows the traffic, but the server itself says "no".

- The application (like Gunicorn, Node, etc.) crashed and isn't running.
- The service is running but bound to localhost (`127.0.0.1`) instead of all interfaces (`0.0.0.0`).

---
