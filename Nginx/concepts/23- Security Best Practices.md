# Overview

Nginx is often the first component exposed to the Internet.

Because every incoming request reaches Nginx before the application, it plays a critical role in securing the entire infrastructure.

A properly configured Nginx server can help protect against:

- Unauthorized access
- Brute-force attacks
- Information leakage
- Denial of Service (DoS)
- Directory traversal
- Malicious HTTP requests

Security is not achieved by a single directive. Instead, it requires multiple layers of protection working together.

---

# Defense in Depth

A secure production architecture consists of multiple security layers.

```text
                 Internet

                     │

                     ▼

                 Firewall

                     │

                     ▼

                  Nginx

                     │

          Rate Limiting

                     │

          Security Headers

                     │

            Reverse Proxy

                     │

                Application

                     │

                  Database
```

If one layer fails, additional layers continue protecting the application.

---

# Keep Nginx Updated

Security vulnerabilities are discovered regularly.

Always use a supported and actively maintained version of Nginx.

Benefits:

- Security patches
- Bug fixes
- Performance improvements
- New features

Regular updates reduce exposure to known vulnerabilities.

---

# Hide Nginx Version

By default, error pages may reveal the installed Nginx version.

Example:

```http
Server: nginx/1.24.0
```

Hide version information:

```nginx
server_tokens off;
```

Response:

```http
Server: nginx
```

Attackers gain less information about the server.

---

# Disable Unnecessary HTTP Methods

Most applications only require:

- GET
- POST
- PUT
- DELETE

Block methods that are not needed.

Example:

```nginx
location / {

    limit_except GET POST {

        deny all;

    }

}
```

Benefits:

- Smaller attack surface
- Better API protection

---

# Restrict Sensitive Files

Configuration files should never be publicly accessible.

Example:

```nginx
location ~ /\. {

    deny all;

}
```

Protects files such as:

```
.git

.env

.htaccess
```

---

# Prevent Directory Listing

If no index file exists, Nginx may display a directory listing.

Disable it:

```nginx
autoindex off;
```

Without protection:

```text
/images/

↓

File List Visible
```

With:

```nginx
autoindex off;
```

Users receive:

```
403 Forbidden
```

instead of a file listing.

---

# Protect Administrative Areas

Restrict access to sensitive endpoints.

Example:

```nginx
location /admin {

    allow 192.168.1.0/24;

    deny all;

}
```

Only trusted networks may access the admin interface.

---

# Rate Limiting

Limit how quickly clients can send requests.

Example:

```nginx
limit_req_zone
$binary_remote_addr
zone=api_limit:10m
rate=10r/s;
```

Apply the limit:

```nginx
location /api {

    limit_req zone=api_limit;

}
```

Benefits:

- Slows brute-force attacks
- Protects APIs
- Reduces abusive traffic

---

# Limit Concurrent Connections

Restrict the number of simultaneous connections per client.

Example:

```nginx
limit_conn_zone
$binary_remote_addr
zone=conn_limit:10m;
```

Apply:

```nginx
location / {

    limit_conn conn_limit 20;

}
```

One client cannot exceed:

```
20 Connections
```

---

# Limit Upload Size

Prevent excessively large uploads.

Example:

```nginx
client_max_body_size 20M;
```

Benefits:

- Protects storage
- Reduces abuse
- Prevents oversized requests

---

# Secure SSL/TLS Configuration

Enable only modern TLS versions.

Example:

```nginx
ssl_protocols TLSv1.2 TLSv1.3;
```

Avoid:

- SSLv2
- SSLv3
- TLSv1.0
- TLSv1.1

These protocols have known security weaknesses.

---

# Enable HSTS

Force browsers to use HTTPS.

Example:

```nginx
add_header Strict-Transport-Security
"max-age=31536000"
always;
```

Benefits:

- Prevents protocol downgrade attacks
- Improves transport security

---

# Use Security Headers

Recommended headers include:

```nginx
add_header X-Frame-Options "DENY";

add_header X-Content-Type-Options "nosniff";

add_header Referrer-Policy
"strict-origin-when-cross-origin";

add_header Content-Security-Policy
"default-src 'self';";
```

These reduce common browser-based attacks.

---

# Protect Against Clickjacking

Prevent websites from embedding your pages.

```nginx
add_header X-Frame-Options "DENY";
```

This blocks framing attempts.

---

# Disable MIME Sniffing

```nginx
add_header X-Content-Type-Options "nosniff";
```

Browsers use the declared content type instead of guessing.

---

# Hide Backend Servers

Applications should never be exposed directly.

Correct architecture:

```text
Internet

↓

Nginx

↓

Gunicorn

↓

Django
```

Instead of:

```text
Internet

↓

Gunicorn
```

Only Nginx should be publicly accessible.

---

# Restrict Direct Access to Backend Ports

Application ports such as:

```
8000

5000

8080
```

should be accessible only from trusted internal networks or localhost.

Example:

```text
Internet

×

Port 8000

↓

Blocked
```

---

# Secure File Permissions

Certificate files:

```
example.crt
```

Private keys:

```
example.key
```

Private keys should only be readable by authorized users.

Never expose them publicly.

---

# Validate Configuration

Always test configuration changes before reloading Nginx.

```bash
nginx -t
```

Expected output:

```text
syntax is ok

test is successful
```

---

# Monitor Logs

Review:

```text
access.log

error.log
```

Look for:

- Repeated failed requests
- 404 errors
- 401 Unauthorized
- 403 Forbidden
- 500 errors
- Unusual traffic patterns

Early detection helps prevent larger incidents.

---

# Protect Against Information Leakage

Avoid exposing:

- Software versions
- Internal IP addresses
- Stack traces
- Sensitive response headers

Only necessary information should be returned to clients.

---

# Use a Firewall

Restrict access at the operating system or cloud firewall level.

Example:

Allow:

```
80

443
```

Block:

```
8000

3306

6379
```

Backend services should not be publicly reachable.

---

# Security Checklist

| Recommendation | Status |
|----------------|--------|
| Hide Nginx Version | ✅ |
| Enable HTTPS | ✅ |
| TLS 1.2 / 1.3 Only | ✅ |
| Enable HSTS | ✅ |
| Security Headers | ✅ |
| Disable Directory Listing | ✅ |
| Protect Sensitive Files | ✅ |
| Rate Limiting | ✅ |
| Connection Limiting | ✅ |
| Restrict Backend Ports | ✅ |
| Monitor Logs | ✅ |
| Validate Configuration | ✅ |

---

# Real-World Example

Production deployment:

```text
                 Internet

                     │

                Firewall

                     │

                 Nginx

       HTTPS + Rate Limit

       Security Headers

        Reverse Proxy

                     │

               FastAPI

                     │

                 PostgreSQL
```

Security responsibilities:

Nginx:

- HTTPS
- Request filtering
- Rate limiting
- Security headers
- Reverse proxy

Application:

- Authentication
- Authorization
- Business logic

Database:

- Data storage

---

# Best Practices

- Keep Nginx updated.
- Enable HTTPS everywhere.
- Hide server version information.
- Disable unnecessary HTTP methods.
- Protect hidden and sensitive files.
- Disable directory listing.
- Apply rate limiting to public APIs.
- Restrict backend ports to private networks.
- Monitor logs regularly.
- Test every configuration before deployment.

---

# Common Mistakes

## Running Without HTTPS

Transmitting sensitive information over HTTP exposes users to interception attacks.

---

## Exposing Application Servers

Publishing Gunicorn, Uvicorn, or Node.js ports directly to the Internet bypasses the protections provided by Nginx.

---

## Forgetting Rate Limits

Public login and API endpoints without rate limiting are vulnerable to brute-force and abuse.

---

## Ignoring Log Files

Security incidents often leave evidence in Access and Error Logs before users notice a problem.

---

# Interview Notes

### Beginner Questions

- Why is Nginx considered the first line of defense?
- What does `server_tokens off` do?
- Why should directory listing be disabled?
- What is rate limiting?

---

### Intermediate Questions

- How would you secure an Nginx production server?
- Why should backend ports not be publicly exposed?
- Explain `limit_req` and `limit_conn`.
- Why should private keys be protected?
- What security measures should every production Nginx deployment include?

---

# Key Takeaways

- Nginx is a critical security layer positioned between the Internet and backend applications.
- A secure deployment combines HTTPS, security headers, rate limiting, connection limiting, restricted file access, and proper logging.
- Backend application servers should remain private, with Nginx acting as the only public entry point.
- Regular updates, configuration validation, and continuous log monitoring are essential for maintaining a secure production environment.
- Security is achieved through multiple layers of defense rather than a single configuration directive.