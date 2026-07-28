# Overview

This cheat sheet contains the most commonly used commands for developing, testing, debugging, and deploying gRPC applications. It covers Protocol Buffer compilation, Python development, grpcurl, Docker, Kubernetes, networking, TLS, and production troubleshooting.

Use this document as a quick reference during development or while diagnosing production issues.

---

# Protocol Buffer Compiler

## Generate Python Files

```bash
python -m grpc_tools.protoc \
-I. \
--python_out=. \
--grpc_python_out=. \
employee.proto
```

---

## Generate Multiple Proto Files

```bash
python -m grpc_tools.protoc \
-I=. \
--python_out=. \
--grpc_python_out=. \
protos/*.proto
```

---

## Generate Go Files

```bash
protoc \
--go_out=. \
--go-grpc_out=. \
employee.proto
```

---

## Generate Java Files

```bash
protoc \
--java_out=. \
employee.proto
```

---

## Generate C++ Files

```bash
protoc \
--cpp_out=. \
employee.proto
```

---

# Python Environment

## Create Virtual Environment

```bash
python -m venv .venv
```

---

## Activate (Windows)

```powershell
.venv\Scripts\activate
```

---

## Activate (Linux/macOS)

```bash
source .venv/bin/activate
```

---

## Install gRPC

```bash
pip install grpcio
```

---

## Install gRPC Tools

```bash
pip install grpcio-tools
```

---

## Install Requirements

```bash
pip install -r requirements.txt
```

---

## Freeze Dependencies

```bash
pip freeze > requirements.txt
```

---

# Running Applications

## Start gRPC Server

```bash
python server.py
```

---

## Start gRPC Client

```bash
python client.py
```

---

## Run with Uvicorn (Hybrid Projects)

```bash
uvicorn main:app --reload
```

---

# grpcurl Commands

## List Services

```bash
grpcurl localhost:50051 list
```

---

## Describe a Service

```bash
grpcurl localhost:50051 describe EmployeeService
```

---

## Describe a Method

```bash
grpcurl localhost:50051 describe EmployeeService.GetEmployee
```

---

## Invoke Unary RPC

```bash
grpcurl \
-d '{"id":1}' \
localhost:50051 \
EmployeeService/GetEmployee
```

---

## Invoke with Reflection Disabled

```bash
grpcurl \
-import-path protos \
-proto employee.proto \
-d '{"id":1}' \
localhost:50051 \
EmployeeService/GetEmployee
```

---

## Call with Metadata

```bash
grpcurl \
-H "authorization: Bearer <JWT>" \
localhost:50051 \
EmployeeService/GetEmployee
```

---

## Call with TLS

```bash
grpcurl \
-cacert ca.crt \
host:443 \
EmployeeService/GetEmployee
```

---

## Call with Mutual TLS

```bash
grpcurl \
-cert client.crt \
-key client.key \
-cacert ca.crt \
host:443 \
EmployeeService/GetEmployee
```

---

# Docker Commands

## Build Image

```bash
docker build -t grpc-app .
```

---

## Run Container

```bash
docker run -p 50051:50051 grpc-app
```

---

## List Containers

```bash
docker ps
```

---

## View Logs

```bash
docker logs <container-id>
```

---

## Execute Shell

```bash
docker exec -it <container-id> sh
```

---

## Stop Container

```bash
docker stop <container-id>
```

---

## Remove Container

```bash
docker rm <container-id>
```

---

# Docker Compose

## Start Services

```bash
docker compose up
```

---

## Start in Detached Mode

```bash
docker compose up -d
```

---

## Stop Services

```bash
docker compose down
```

---

## View Logs

```bash
docker compose logs
```

---

# Kubernetes

## List Pods

```bash
kubectl get pods
```

---

## List Services

```bash
kubectl get services
```

---

## Describe Pod

```bash
kubectl describe pod <pod-name>
```

---

## View Logs

```bash
kubectl logs <pod-name>
```

---

## Follow Logs

```bash
kubectl logs -f <pod-name>
```

---

## Execute Shell

```bash
kubectl exec -it <pod-name> -- sh
```

---

## Restart Deployment

```bash
kubectl rollout restart deployment <deployment-name>
```

---

## Deployment Status

```bash
kubectl rollout status deployment <deployment-name>
```

---

## Port Forward

```bash
kubectl port-forward svc/grpc-service 50051:50051
```

---

# Networking

## Test Port (Linux/macOS)

```bash
nc -zv localhost 50051
```

---

## Test Port (Windows PowerShell)

```powershell
Test-NetConnection localhost -Port 50051
```

---

## View Listening Ports

```bash
netstat -an
```

---

## DNS Lookup

```bash
nslookup grpc-service
```

---

## Ping Host

```bash
ping grpc-service
```

---

# TLS & Certificates

## View Certificate

```bash
openssl x509 -in server.crt -text -noout
```

---

## Check Expiration

```bash
openssl x509 -enddate -noout -in server.crt
```

---

## Test TLS Connection

```bash
openssl s_client -connect localhost:50051
```

---

# Git Commands

## Clone Repository

```bash
git clone <repository-url>
```

---

## Pull Latest Changes

```bash
git pull
```

---

## Create Branch

```bash
git checkout -b feature/grpc
```

---

## Commit Changes

```bash
git commit -m "Add gRPC service"
```

---

## Push Branch

```bash
git push origin feature/grpc
```

---

# Performance & Debugging

## Monitor Docker Resource Usage

```bash
docker stats
```

---

## Watch Kubernetes Resources

```bash
kubectl top pods
```

---

## Display Events

```bash
kubectl get events
```

---

## Verify Reflection

```bash
grpcurl localhost:50051 list
```

---

## Check Service Endpoints

```bash
kubectl get endpoints
```

---

# Common Troubleshooting Commands

| Problem | Command |
|----------|---------|
| List gRPC Services | `grpcurl localhost:50051 list` |
| Describe Service | `grpcurl localhost:50051 describe ServiceName` |
| Check Running Containers | `docker ps` |
| View Container Logs | `docker logs <container-id>` |
| View Kubernetes Logs | `kubectl logs <pod-name>` |
| List Pods | `kubectl get pods` |
| List Services | `kubectl get svc` |
| Check Endpoints | `kubectl get endpoints` |
| Test Network Port | `Test-NetConnection` / `nc` |
| Verify TLS Certificate | `openssl x509` |

---

# Development Workflow

```text
Edit .proto

↓

Generate Code

↓

Implement Server

↓

Implement Client

↓

Run Application

↓

Test with grpcurl

↓

Debug

↓

Containerize

↓

Deploy

↓

Monitor
```

---

# Best Practices

- Regenerate code whenever a `.proto` file changes.
- Keep generated files out of manual edits.
- Test services locally with `grpcurl` before deployment.
- Use Docker for consistent development environments.
- Validate Kubernetes deployments using logs and health checks.
- Verify TLS certificates before enabling secure communication.
- Use version control for `.proto` files and generated source code according to your team's workflow.

---

# Common Mistakes

- Forgetting to regenerate code after modifying `.proto` files.
- Editing generated files manually.
- Testing production services without TLS.
- Ignoring container and Kubernetes logs during debugging.
- Forgetting to expose the correct container port.
- Assuming Reflection is enabled in every environment.

---

# Key Takeaways

- A small set of commands covers most day-to-day gRPC development, debugging, and deployment tasks.
- `protoc`, `grpcurl`, Docker, and Kubernetes commands are essential tools for backend engineers working with gRPC.
- Familiarity with these commands improves productivity, simplifies troubleshooting, and accelerates development in both local and production environments.