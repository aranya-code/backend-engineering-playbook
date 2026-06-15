# Networks in Docker Compose

## Overview

Networking is one of Docker Compose's most powerful features.

Docker Compose automatically creates networks and enables containers to communicate with each other using service names instead of IP addresses.

This eliminates the need for manual network configuration in most applications.

---

# Why Networks Matter

Consider a web application:

```text
Frontend

Backend API

Database
```

These components must communicate.

Without networking:

```text
Frontend ❌ Backend

Backend ❌ Database
```

With networking:

```text
Frontend ✔ Backend

Backend ✔ Database
```

---

# Docker Compose Default Network

When Docker Compose starts an application:

```bash
docker compose up
```

it automatically creates a network.

Example:

```text
myapp_default
```

---

# Default Network Architecture

```text
Docker Compose

        │

        ▼

Default Network

        │

 ┌──────┼──────┐

 ▼      ▼      ▼

Web    API   MySQL
```

All services can communicate.

---

# Service Discovery

One major benefit of Docker Compose networking is built-in DNS.

Example:

```yaml
services:

  frontend:

  backend:

  mysql:
```

Service names become DNS names.

---

# Communication Example

Instead of:

```text
192.168.1.25
```

use:

```text
mysql
```

Connection:

```text
frontend → backend

backend → mysql
```

---

# Verify Network Creation

Start application:

```bash
docker compose up -d
```

List networks:

```bash
docker network ls
```

Example:

```text
myapp_default
```

---

# Inspect Network

```bash
docker network inspect myapp_default
```

Displays:

- Connected Containers
- Network Driver
- Subnet Information
- DNS Configuration

---

# Custom Networks

Instead of relying on the default network, define your own.

Example:

```yaml
networks:

  app-network:
```

---

# Attach Services

```yaml
services:

  frontend:

    networks:

      - app-network

  backend:

    networks:

      - app-network
```

---

# Architecture

```text
App Network

     │

 ┌───┼───┐

 ▼   ▼   ▼

Frontend

Backend

Database
```

---

# Network Drivers

Docker supports multiple network drivers.

---

# Bridge Network

Default Docker Compose network type.

Example:

```yaml
networks:

  app-network:

    driver: bridge
```

---

# Bridge Architecture

```text
Host Machine

      │

      ▼

Bridge Network

      │

 ┌────┼────┐

 ▼    ▼    ▼

C1   C2   C3
```

Most common option.

---

# Host Network

Container shares host networking.

Example:

```yaml
network_mode: host
```

---

# Host Mode Architecture

```text
Container

      │

      ▼

Host Network
```

No network isolation.

---

# None Network

Disable networking.

Example:

```yaml
network_mode: none
```

Container receives:

```text
No Network Access
```

---

# Multiple Networks

Applications often use more than one network.

Example:

```yaml
networks:

  frontend-network:

  backend-network:
```

---

# Service Assignment

```yaml
services:

  frontend:

    networks:

      - frontend-network

  backend:

    networks:

      - frontend-network

      - backend-network

  database:

    networks:

      - backend-network
```

---

# Architecture

```text
Frontend Network

Frontend

Backend


Backend Network

Backend

Database
```

Improves isolation.

---

# Network Aliases

Assign additional DNS names.

Example:

```yaml
services:

  mysql:

    networks:

      app-network:

        aliases:

          - database
```

Now:

```text
mysql

database
```

both work.

---

# External Networks

Use an existing Docker network.

Example:

```yaml
networks:

  existing-network:

    external: true
```

---

# Network Creation Workflow

```text
Compose File

      │

      ▼

Network Creation

      │

      ▼

Containers Join Network

      │

      ▼

DNS Available
```

---

# Testing Connectivity

Enter container:

```bash
docker exec -it <container-id> sh
```

Ping service:

```bash
ping mysql
```

Result:

```text
DNS Resolution Successful
```

---

# Viewing Connected Containers

```bash
docker network inspect myapp_default
```

Look for:

```text
Containers
```

section.

---

# Common Network Commands

## List Networks

```bash
docker network ls
```

---

## Inspect Network

```bash
docker network inspect <network-name>
```

---

## Remove Network

```bash
docker network rm <network-name>
```

---

## View Compose Services

```bash
docker compose ps
```

---

# Example Three-Tier Application

```yaml
services:

  frontend:

    image: nginx

  backend:

    image: httpd

  database:

    image: mysql

networks:

  app-network:
```

---

# Communication Flow

```text
Frontend

    │

    ▼

Backend

    │

    ▼

Database
```

Through Docker networking.

---

# Networking Best Practices

## Use Service Names

Good:

```text
mysql
```

Avoid:

```text
172.18.0.5
```

---

## Use Custom Networks

Improves organization.

---

## Separate Application Layers

Example:

```text
Frontend Network

Backend Network
```

---

## Inspect Networks Regularly

Useful for troubleshooting.

---

## Avoid Host Mode Unless Necessary

Bridge networking provides better isolation.

---

# Common Network Problems

## Service Cannot Reach Database

Check:

```bash
docker network inspect
```

---

## DNS Resolution Failure

Verify:

```text
Same Network
```

---

## Wrong Service Name

Use:

```text
Service Name

Not Container IP
```

---

# Common Interview Questions

## Does Docker Compose Automatically Create Networks?

Yes.

Compose automatically creates a default network for the application.

---

## How Do Containers Communicate?

Using built-in DNS and service names.

---

## Which Network Driver Is Used By Default?

```text
Bridge
```

---

## Can Services Join Multiple Networks?

Yes.

A service can be attached to multiple networks.

---

## What Command Lists Docker Networks?

```bash
docker network ls
```

---

## What Command Inspects a Network?

```bash
docker network inspect
```

---

# Interview One-Liner

Docker Compose networking automatically creates isolated networks with built-in DNS service discovery, allowing containers to communicate using service names instead of IP addresses while supporting custom network topologies and multi-tier application architectures.
