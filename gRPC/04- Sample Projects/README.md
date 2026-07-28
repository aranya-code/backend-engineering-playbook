# Sample Projects

Hands-on Python gRPC projects that progressively demonstrate real-world patterns — from a minimal Hello World to Django integration and all four streaming types.

---

## 📂 Projects

| #  | Project                                                              | RPC Pattern(s)              | Key Concepts                                        |
|----|----------------------------------------------------------------------|-----------------------------|-----------------------------------------------------|
| 01 | [Hello-World](./01-%20Hello-World/)                                  | Unary                       | Minimal gRPC setup, protobuf code generation         |
| 02 | [Calculator-Service](./02-%20Calculator-Service/)                    | Unary (×4)                  | Multiple RPCs, error handling with status codes      |
| 03 | [Employee-Management](./03-%20Employee-Management/)                  | Unary (CRUD)                | Multi-module project, in-memory data store           |
| 04 | [Chat-Application](./04-%20Chat-Application/)                        | Bidirectional Streaming     | Stream generators, real-time echo communication      |
| 05 | [Django-gRPC-Integration](./05-%20Django-gRPC-Integration/)          | Unary                       | Django ORM + gRPC, dual transport layers             |
| 06 | [Greeter Service](./06-%20Greeter%20Service/)                        | All 4 patterns              | Unary, Client/Server/Bidirectional Streaming         |

---

## 🎯 Recommended Learning Order

```
Hello World (basics)
       │
       ▼
Calculator (multiple unary RPCs + error handling)
       │
       ▼
Employee Management (CRUD, multi-module architecture)
       │
       ▼
Chat Application (bidirectional streaming)
       │
       ▼
Django Integration (framework integration)
       │
       ▼
Greeter Service (all 4 RPC patterns in one project)
```

---

## 🛠️ Common Setup

Every project follows the same workflow:

```bash
# 1. Create & activate a virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Generate protobuf code (command varies — see each project's README)
python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/<name>.proto

# 4. Start the server
python server.py                # or python server/server.py

# 5. Run the client (in another terminal)
python client.py                # or python client/client.py
```

Each project's README contains the exact commands.

---

## 📦 Shared Dependencies

| Package        | Purpose                           |
|---------------|-----------------------------------|
| `grpcio`       | gRPC runtime                      |
| `grpcio-tools` | Protobuf compiler plugin for gRPC |
| `Django`       | Required only for project 05      |
