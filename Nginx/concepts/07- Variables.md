# Overview

Variables are one of the most powerful features of Nginx.

A **variable** stores information about the current request, response, server, or client connection.

Variables allow Nginx to make decisions dynamically instead of relying on hardcoded values.

For example, instead of writing:

```nginx
return 200 "Hello";
```

You can use variables:

```nginx
return 200 "$remote_addr";
```

Nginx replaces the variable with its actual value before sending the response.

---

# Variable Syntax

Every built-in variable begins with a **`$`** symbol.

General syntax:

```nginx
$variable_name
```

Examples:

```nginx
$host
```

```nginx
$request_uri
```

```nginx
$remote_addr
```

```nginx
$args
```

---

# How Variables Work

Suppose a client sends the following request:

```http
GET /products?id=10 HTTP/1.1

Host: api.example.com
```

Nginx automatically creates variables representing different parts of the request.

| Variable | Value |
|----------|-------|
| `$host` | api.example.com |
| `$request_uri` | /products?id=10 |
| `$uri` | /products |
| `$args` | id=10 |
| `$request_method` | GET |

These values are available throughout request processing.

---

# Types of Variables

Nginx variables generally fall into several categories.

- Request Variables
- Response Variables
- Client Variables
- Server Variables
- Connection Variables
- Time Variables

---

# Request Variables

These variables describe the incoming HTTP request.

## $request

Contains the complete request line.

Example:

```http
GET /products?id=5 HTTP/1.1
```

Variable:

```nginx
$request
```

Value:

```
GET /products?id=5 HTTP/1.1
```

---

## $request_method

Returns the HTTP method.

Example:

```
GET
```

```
POST
```

```
PUT
```

```
DELETE
```

Configuration:

```nginx
$request_method
```

---

## $request_uri

Returns the original URI including query parameters.

Example request:

```
/products?id=5
```

Value:

```
/products?id=5
```

---

## $uri

Returns the normalized URI **without query parameters**.

Example:

Request:

```
/products?id=5
```

Value:

```
/products
```

Difference:

| Variable | Includes Query Parameters |
|----------|---------------------------|
| `$request_uri` | ✅ Yes |
| `$uri` | ❌ No |

---

## $args

Returns only the query string.

Example:

```
?page=5&sort=name
```

Value:

```
page=5&sort=name
```

---

# Client Variables

These variables describe the client making the request.

## $remote_addr

Returns the client's IP address.

Example:

```nginx
$remote_addr
```

Possible value:

```
192.168.1.20
```

---

## $remote_port

Returns the client's TCP port.

Example:

```
52345
```

---

## $http_user_agent

Returns the browser or client information.

Example:

```
Mozilla/5.0
```

Useful for:

- Logging
- Analytics
- Debugging

---

## $http_referer

Returns the referring page.

Example:

```
https://google.com
```

---

# Server Variables

These variables describe the current server.

## $host

Returns the hostname from the request.

Example:

```
api.example.com
```

---

## $server_name

Returns the matching server block name.

Example:

```nginx
server_name api.example.com;
```

Variable:

```
$server_name
```

---

## $server_port

Returns the port that accepted the request.

Example:

```
80
```

or

```
443
```

---

## $scheme

Returns the protocol used.

Possible values:

```
http
```

```
https
```

Useful when redirecting traffic.

---

# Response Variables

These variables become available while generating the response.

## $status

Returns the HTTP status code.

Examples:

```
200
```

```
404
```

```
500
```

---

## $bytes_sent

Returns the total number of bytes sent to the client.

Useful for logging and monitoring.

---

# Time Variables

Useful for logging and performance analysis.

## $time_local

Example:

```
13/Jul/2026:22:45:18 +0530
```

---

## $request_time

Returns the total request processing time.

Example:

```
0.231
```

Meaning:

The request took **231 milliseconds**.

---

# Using Variables in Logs

Variables are heavily used inside log formats.

Example:

```nginx
log_format main '$remote_addr - $host [$time_local] "$request" $status';
```

Possible output:

```text
192.168.1.5 - api.example.com [13/Jul/2026:22:45:18 +0530] "GET /products HTTP/1.1" 200
```

---

# Using Variables in Redirects

Variables can be used while redirecting requests.

Example:

```nginx
return 301 https://$host$request_uri;
```

If the request is:

```
http://example.com/products?id=10
```

The client is redirected to:

```
https://example.com/products?id=10
```

---

# Using Variables with Reverse Proxy

Variables are frequently used when forwarding requests.

Example:

```nginx
proxy_set_header Host $host;

proxy_set_header X-Real-IP $remote_addr;
```

This ensures the backend application receives the original request information.

---

# Real-World Example

Configuration:

```nginx
server {

    location / {

        proxy_set_header Host $host;

        proxy_set_header X-Forwarded-For $remote_addr;

        proxy_pass http://backend;

    }

}
```

Request:

```
GET /products
```

Nginx forwards:

- Original Host
- Client IP
- Request URI

to the backend application.

This is a common production configuration for Django, FastAPI, and other web frameworks.

---

# Frequently Used Variables

| Variable | Description |
|-----------|-------------|
| `$host` | Hostname |
| `$server_name` | Matching server name |
| `$server_port` | Server port |
| `$scheme` | HTTP or HTTPS |
| `$remote_addr` | Client IP |
| `$remote_port` | Client Port |
| `$request` | Complete request line |
| `$request_method` | HTTP method |
| `$request_uri` | URI with query string |
| `$uri` | URI without query string |
| `$args` | Query parameters |
| `$status` | Response status code |
| `$bytes_sent` | Response size |
| `$time_local` | Local server time |
| `$request_time` | Request processing time |
| `$http_user_agent` | Client browser |
| `$http_referer` | Referring page |

---

# Best Practices

- Prefer built-in variables instead of hardcoded values.
- Use variables in log formats for better observability.
- Forward important request headers to backend applications.
- Use `$host` instead of manually writing domain names where appropriate.
- Be cautious when exposing request information in responses.

---

# Common Mistakes

## Confusing `$uri` and `$request_uri`

Request:

```
/products?id=10
```

```
$uri
```

Returns:

```
/products
```

```
$request_uri
```

Returns:

```
/products?id=10
```

---

## Forgetting the `$` Prefix

Incorrect:

```nginx
host
```

Correct:

```nginx
$host
```

---

## Exposing Sensitive Information

Avoid returning internal variables directly to users unless required.

Variables may contain request details that should only be used internally or for logging.

---

# Interview Notes

### Beginner Questions

- What is a variable in Nginx?
- How are variables referenced?
- What does `$host` represent?
- What is the difference between `$uri` and `$request_uri`?

---

### Intermediate Questions

- Why are variables useful in reverse proxy configurations?
- Explain how `$remote_addr` is used.
- How are variables used in custom log formats?
- Which variables would you forward to a backend application?

---

# Key Takeaways

- Variables store request, response, client, and server information.
- Every variable begins with the `$` symbol.
- Variables make Nginx configurations dynamic and reusable.
- Built-in variables are widely used for logging, reverse proxying, redirects, caching, and security.
- Understanding commonly used variables is essential for writing production-ready Nginx configurations.