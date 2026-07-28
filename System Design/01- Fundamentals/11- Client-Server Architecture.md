# Client-Server Architecture

## Overview

Client-Server Architecture is one of the most fundamental architectural models in computer science and serves as the foundation for almost every modern application.

Whenever you browse a website, use a mobile application, watch videos on Netflix, send messages on WhatsApp, or make an online payment, your device acts as a **client** that communicates with one or more **servers**.

Understanding Client-Server Architecture is essential before learning topics such as APIs, Load Balancers, Reverse Proxies, Microservices, Caching, and Distributed Systems.

---

# What is Client-Server Architecture?

Client-Server Architecture is a computing model where:

- A **Client** requests a service.
- A **Server** processes the request.
- The **Server** sends back a response.

In simple terms:

> A client requests resources, and a server provides those resources.

---

# Basic Architecture

```
        Request
Client -------------> Server
        <-------------
          Response
```

The communication is always initiated by the client.

The server waits for incoming requests and responds when one arrives.

---

# Who is the Client?

A client is any application or device that requests services from another system.

Examples include:

- Web browsers
- Mobile applications
- Desktop applications
- Smart TVs
- IoT devices
- Command-line tools

Examples:

- Google Chrome
- Firefox
- Safari
- Android App
- iPhone App
- Postman
- cURL

---

# Who is the Server?

A server is a computer or software application that provides services to clients.

Examples include:

- Web Servers
- API Servers
- Database Servers
- Authentication Servers
- File Servers
- DNS Servers

A single physical machine may run multiple servers simultaneously.

---

# How Client-Server Communication Works

Suppose a user visits:

```
https://example.com
```

The communication typically follows these steps:

```
1. User opens browser

        │
        ▼

2. Browser sends HTTP Request

        │
        ▼

3. Web Server receives request

        │
        ▼

4. Application processes request

        │
        ▼

5. Database queried (if needed)

        │
        ▼

6. Server creates response

        │
        ▼

7. Browser renders webpage
```

Every web application follows this basic workflow.

---

# Request-Response Model

Client-server communication generally follows a Request-Response pattern.

```
Client

Request
────────────►

Server

Response
◄────────────
```

The client sends a request.

The server processes it and returns a response.

The interaction ends until another request is made.

---

# Example: Food Delivery Application

Suppose a customer opens a food delivery app.

### Request

```
GET /restaurants
```

The server:

- Authenticates the request
- Reads restaurant data
- Retrieves nearby restaurants
- Returns JSON

### Response

```json
[
  {
    "name": "Pizza Palace",
    "rating": 4.8
  },
  {
    "name": "Burger House",
    "rating": 4.5
  }
]
```

The mobile application displays the list to the user.

---

# Components of Client-Server Architecture

## Client

Responsible for:

- User Interface
- Sending requests
- Receiving responses
- Displaying results

Examples:

- Browser
- Mobile App
- Desktop Software

---

## Network

Responsible for transporting data.

Examples:

- Internet
- Wi-Fi
- LAN
- Mobile Network

Protocols commonly used:

- HTTP
- HTTPS
- WebSocket
- gRPC

---

## Server

Responsible for:

- Processing requests
- Business logic
- Authentication
- Database access
- Returning responses

---

## Database

Stores persistent information.

Examples:

- User accounts
- Orders
- Products
- Messages

The database is usually not directly accessible by clients.

---

# Multiple Clients

A single server usually serves many clients simultaneously.

```
             Client A
                 │
                 │
Client B ─────► Server ◄───── Client C
                 │
                 │
             Client D
```

The server processes requests from all connected clients.

---

# Multi-Tier Client-Server Architecture

Modern applications often separate responsibilities into multiple layers.

```
Client

     │

     ▼

Web Server

     │

     ▼

Application Server

     │

     ▼

Database
```

Each layer performs a different responsibility.

This architecture improves:

- Maintainability
- Scalability
- Security

---

# Three-Tier Architecture

A common implementation of Client-Server Architecture is the Three-Tier Model.

```
Presentation Layer

↓

Business Logic Layer

↓

Data Layer
```

### Presentation Layer

Responsible for:

- User Interface
- User interaction

Examples:

- React
- Angular
- Mobile Apps

---

### Business Logic Layer

Responsible for:

- Validation
- Authentication
- Business rules
- APIs

Examples:

- Django
- FastAPI
- Spring Boot
- Express.js

---

### Data Layer

Responsible for storing information.

Examples:

- PostgreSQL
- MySQL
- MongoDB
- Redis

---

# Advantages of Client-Server Architecture

## Centralized Management

Business logic remains on the server.

Updating the server immediately affects all clients.

---

## Better Security

Sensitive operations remain on the server.

Examples:

- Password validation
- Payment processing
- Database access

Clients never interact directly with the database.

---

## Easier Maintenance

Updating server-side code does not require users to reinstall client applications.

---

## Resource Sharing

Many users can access the same resources simultaneously.

Examples:

- Files
- Databases
- APIs

---

## Scalability

Application servers can be scaled independently from clients.

Load balancers can distribute traffic across multiple servers.

---

# Limitations of Client-Server Architecture

## Server Bottleneck

If all traffic reaches a single server:

```
100,000 Users

↓

One Server
```

Performance eventually degrades.

---

## Single Point of Failure

If only one server exists:

```
Server ❌
```

All clients lose access.

---

## Network Dependency

Clients cannot communicate with the server without network connectivity.

---

## Infrastructure Cost

Large applications require:

- Multiple servers
- Load Balancers
- Monitoring
- Backups

Infrastructure costs increase as systems grow.

---

# Improving Client-Server Architecture

Modern systems improve the traditional architecture using:

- Load Balancers
- Reverse Proxies
- CDNs
- Distributed Caches
- Replicated Databases
- Auto Scaling
- Microservices

These enhancements improve scalability, reliability, and availability.

---

# Real-World Examples

## Web Applications

```
Browser

↓

Nginx

↓

Django

↓

PostgreSQL
```

---

## Mobile Banking

```
Mobile App

↓

API Gateway

↓

Authentication Service

↓

Banking Services

↓

Database
```

---

## Netflix

```
Smart TV

↓

Load Balancer

↓

Microservices

↓

Distributed Databases
```

---

## WhatsApp

```
Mobile App

↓

Messaging Server

↓

Message Queue

↓

Storage
```

---

# Common Mistakes

- Allowing clients to access databases directly.
- Placing too much business logic in the client.
- Running everything on a single server without redundancy.
- Ignoring authentication and authorization.
- Assuming one server is sufficient for future growth.
- Not securing communication with HTTPS.

---

# Best Practices

- Keep business logic on the server.
- Use HTTPS for all client-server communication.
- Authenticate every request.
- Never expose databases directly to clients.
- Scale servers independently from clients.
- Use load balancers for high availability.
- Monitor server health and performance continuously.
- Keep client applications lightweight and focused on presentation.

---

# Key Takeaways

- Client-Server Architecture is the foundation of most modern software systems.
- Clients initiate requests, while servers process those requests and return responses.
- Separating presentation, business logic, and data improves maintainability and scalability.
- Security is strengthened by keeping sensitive operations and data on the server.
- Modern architectures extend the Client-Server model using load balancers, caches, APIs, and distributed services to support large-scale applications.