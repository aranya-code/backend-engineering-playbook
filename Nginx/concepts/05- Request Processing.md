# Overview

Every request that reaches Nginx goes through a well-defined processing pipeline before a response is returned to the client.

Understanding this flow is essential because it explains:

- How Nginx chooses a server block
- How it selects a location block
- How it serves static files
- How it forwards requests to backend applications
- How directives influence request handling

A clear understanding of request processing makes debugging Nginx configurations much easier.

---

# The Complete Request Flow

A simplified request lifecycle looks like this:

```text
                 Client
                    │
                    ▼
               DNS Lookup
                    │
                    ▼
          TCP Connection Established
                    │
                    ▼
           Nginx Receives Request
                    │
                    ▼
          Select Server Block
                    │
                    ▼
         Select Location Block
                    │
        ┌───────────┴────────────┐
        │                        │
        ▼                        ▼
 Serve Static File      Forward to Backend
        │                        │
        └───────────┬────────────┘
                    ▼
            Generate Response
                    │
                    ▼
             Return to Client
```

---

# Step 1 — Client Sends a Request

A user enters a URL into a browser.

Example:

```
http://localhost/images/logo.png
```

The browser creates an HTTP request and sends it to the server.

---

# Step 2 — DNS Resolution

Before contacting Nginx, the browser must determine the server's IP address.

Example:

```text
example.com

↓

192.168.1.10
```

If the IP address is already cached, this step is skipped.

---

# Step 3 — TCP Connection

The browser establishes a TCP connection with the server.

Depending on the request:

- HTTP → Port 80
- HTTPS → Port 443

Nginx begins processing only after the connection is established.

---

# Step 4 — Nginx Accepts the Request

A Worker Process accepts the incoming connection.

```text
Client

   │

   ▼

Worker Process

   │

Reads HTTP Request
```

The Worker Process parses:

- HTTP Method
- URL
- Headers
- Query Parameters
- Request Body

Example request:

```http
GET /products HTTP/1.1

Host: example.com
```

---

# Step 5 — Selecting the Server Block

Nginx first determines which `server` block should handle the request.

Example:

```nginx
server {

    listen 80;

    server_name api.example.com;

}

server {

    listen 80;

    server_name blog.example.com;

}
```

If the request is:

```
Host: api.example.com
```

Nginx selects the first server block.

---

# Step 6 — Selecting the Location Block

After selecting the server, Nginx determines which `location` block best matches the requested URI.

Example:

```nginx
server {

    location / {

    }

    location /images {

    }

    location /api {

    }

}
```

Request:

```
/images/logo.png
```

Selected location:

```nginx
location /images {

}
```

Location matching is one of the most important concepts in Nginx and will be covered in detail in a dedicated chapter.

---

# Step 7 — Execute Directives

Once the correct location is selected, Nginx executes the directives inside it.

Example:

```nginx
location /images {

    root /var/www;

}
```

Request:

```
/images/logo.png
```

Nginx looks for:

```
/var/www/images/logo.png
```

If the file exists, it is returned immediately.

---

# Step 8 — Static File or Reverse Proxy

At this point, Nginx determines how to handle the request.

### Option 1 — Serve a Static File

```text
Browser

   │

   ▼

Nginx

   │

   ▼

HTML / CSS / Image
```

Static files are returned directly without involving an application server.

---

### Option 2 — Forward to Backend

```nginx
location /api {

    proxy_pass http://backend;

}
```

Flow:

```text
Browser

   │

   ▼

Nginx

   │

   ▼

FastAPI

   │

   ▼

Database
```

The backend generates the response, and Nginx forwards it back to the client.

---

# Step 9 — Generate the Response

Depending on the request, the response may come from:

- Static files
- Django
- FastAPI
- Flask
- Node.js
- PHP
- Cache

Before sending the response, Nginx may:

- Compress it
- Add response headers
- Cache it
- Log the request

---

# Step 10 — Return the Response

The final response is sent back to the client.

```text
Client

   ▲

   │

Response

   ▲

Nginx

   ▲

Backend
```

The client receives:

- HTML
- JSON
- Image
- CSS
- JavaScript
- File Download

depending on the request.

---

# Example Walkthrough

Configuration:

```nginx
server {

    listen 80;

    server_name localhost;

    location / {

        root html;

        index index.html;

    }

}
```

Client Request:

```
http://localhost/
```

Processing steps:

1. Client connects to port 80.
2. Nginx selects the matching `server` block.
3. The `/` location matches the request.
4. Nginx applies the `root` directive.
5. Nginx searches for:

```
html/index.html
```

6. The file is returned to the browser.

---

# Request Processing Decision Tree

```text
Incoming Request
        │
        ▼
Choose Server Block
        │
        ▼
Choose Location Block
        │
        ▼
Execute Directives
        │
        ├──────────────┐
        │              │
        ▼              ▼
Static File      Reverse Proxy
        │              │
        └──────┬───────┘
               ▼
       Send Response
```

---

# Real-World Example

Suppose an online shopping application has the following configuration:

```nginx
server {

    location / {

        root /var/www/frontend;

    }

    location /api {

        proxy_pass http://backend;

    }

    location /images {

        root /var/www;

    }

}
```

Request:

```
GET /
```

Result:

Frontend HTML is served.

---

Request:

```
GET /images/logo.png
```

Result:

Image is served directly by Nginx.

---

Request:

```
GET /api/products
```

Result:

Request is forwarded to the backend application.

---

# Best Practices

- Keep request routing simple and predictable.
- Separate static content from API endpoints.
- Avoid overlapping location rules whenever possible.
- Validate configuration changes before deployment.
- Use descriptive URL structures for easier routing.

---

# Common Mistakes

## Confusing Server Selection with Location Selection

Nginx first selects the **server block**, then the **location block**.

These are two separate stages.

---

## Expecting Every Request to Reach the Backend

Many requests are served directly by Nginx.

Examples include:

- Images
- CSS
- JavaScript
- HTML
- Downloads

Serving static content directly improves performance and reduces load on the application server.

---

## Incorrect Root Configuration

An incorrect `root` directive often leads to **404 Not Found** errors because Nginx searches for files in the wrong directory.

---

# Interview Notes

### Beginner Questions

- How does Nginx process an incoming request?
- What is the first step after Nginx receives a request?
- How does Nginx choose a server block?
- How does Nginx choose a location block?

---

### Intermediate Questions

- Explain the complete request lifecycle inside Nginx.
- What happens before a request reaches the backend application?
- Why are static files served directly by Nginx?
- In what order are server blocks and location blocks evaluated?

---

# Key Takeaways

- Every request follows a structured processing pipeline.
- Nginx first selects the appropriate `server` block.
- It then selects the best matching `location` block.
- Directives inside the selected location determine how the request is handled.
- Requests may be served directly by Nginx or forwarded to a backend application.
- Understanding request processing is fundamental for configuring reverse proxies, static file serving, URL routing, and performance optimization.