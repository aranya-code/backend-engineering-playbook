# gRPC — Backend Engineering Playbook

A comprehensive, self-contained learning resource for mastering **gRPC** with **Python** — from core concepts and Protocol Buffers to production deployment, troubleshooting, and interview preparation. Includes six hands-on sample projects demonstrating every RPC pattern.

---

## 📂 Sections

| #  | Section | Description |
|----|---------|-------------|
| 01 | [Concepts](./01-%20Concepts/) | Core gRPC fundamentals — architecture, HTTP/2, Protocol Buffers, RPC types, channels, deadlines, metadata, security, error handling, and performance (16 chapters) |
| 02 | [Protocol Buffers](./02-%20Protobuf/) | Deep dive into Protobuf — syntax, scalar types, messages, enums, nested messages, maps, `oneof`, versioning, and Well-Known Types (13 chapters) |
| 03 | [Python gRPC](./03-%20Python/) | Building gRPC services with Python — environment setup, code generation, all 4 RPC types, async gRPC, and interceptors (8 chapters) |
| 04 | [Sample Projects](./04-%20Sample%20Projects/) | Six hands-on projects: Hello World, Calculator, Employee CRUD, Chat App, Django Integration, and Greeter Service |
| 05 | [Production](./05-%20Production/) | Production-grade topics — authentication, service discovery, load balancing, health checks, reflection, keepalive, compression, and deployment patterns (8 chapters) |
| 06 | [Troubleshooting](./06-%20Troubleshooting/) | Diagnosing real-world failures — connection errors, TLS issues, HTTP/2 problems, Kubernetes debugging, and performance analysis (15 chapters) |
| 07 | [Interview](./07-%20Interview/) | Interview preparation — beginner to senior questions, system design, mock interviews, rapid fire, and cheat sheets (9 chapters) |
| 08 | [Cheatsheets](./08-%20Cheatsheets/) | Quick-reference guides — gRPC overview, Protobuf syntax, common commands, status codes, interview revision, and production checklists (6 sheets) |

---

## 🎯 Recommended Learning Path

```
01- Concepts                 ← Understand how gRPC works
       │
       ▼
02- Protobuf                 ← Master schema design
       │
       ▼
03- Python                   ← Build clients & servers
       │
       ▼
04- Sample Projects          ← Practice with real code
       │
       ▼
05- Production               ← Deploy & operate at scale
       │
       ▼
06- Troubleshooting          ← Debug real-world failures
       │
       ▼
07- Interview                ← Prepare for interviews
       │
       ▼
08- Cheatsheets              ← Quick revision & reference
```

---

## 🛠️ Prerequisites

- **Python 3.8+**
- **pip**
- Basic understanding of APIs and client-server architecture
- Familiarity with command-line tools

---

## 🚀 Quick Start

Jump straight into the first sample project:

```bash
cd "04- Sample Projects/01- Hello-World"
pip install -r requirements.txt
python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/hello.proto
python server.py
# In another terminal:
python client.py
```

---

## 📊 What's Covered

| Category | Topics |
|----------|--------|
| **Core** | RPC, HTTP/2, Protocol Buffers, Channels, Metadata, Serialization |
| **RPC Types** | Unary, Server Streaming, Client Streaming, Bidirectional Streaming |
| **Security** | TLS, mTLS, JWT, OAuth2, Authentication Interceptors |
| **Production** | Service Discovery, Load Balancing, Health Checks, Keepalive, Compression |
| **Deployment** | Kubernetes, Service Meshes, API Gateways, Blue-Green, Canary |
| **Observability** | Logging, Metrics, Distributed Tracing, OpenTelemetry |
| **Debugging** | grpcurl, Status Codes, Connection Diagnostics, Performance Analysis |

---

## 📄 License

This playbook is intended for educational purposes as part of the [backend-engineering-playbook](../).
