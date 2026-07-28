# Employee Management (gRPC)

A CRUD-style Employee Management service built with Python gRPC. Features an in-memory data store, separate server and client modules, and demonstrates **Unary RPCs** for creating, retrieving, and listing employees.

---

## 📡 RPC Methods

| RPC Method        | Pattern    | Description                                   |
|------------------|-----------|-----------------------------------------------|
| `CreateEmployee` | **Unary** | Create a new employee record                  |
| `GetEmployee`    | **Unary** | Retrieve an employee by ID                    |
| `ListEmployees`  | **Unary** | List all employees                            |

---

## 📁 Project Structure

```
03- Employee-Management/
├── proto/
│   └── employee.proto           # Protobuf service & message definitions
├── server/
│   └── server.py                # gRPC server (in-memory employee store)
├── client/
│   └── client.py                # gRPC client
├── database/
│   └── schema.sql               # SQL schema reference
├── requirements.txt             # Python dependencies
├── run.md                       # Quick-run commands
├── .gitignore
└── README.md
```

---

## 🛠️ Prerequisites

- **Python 3.8+**
- **pip**

---

## 🚀 Getting Started

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate Python Code from Proto

```bash
python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/employee.proto
```

### 3. Start the Server

```bash
python server/server.py
```

The server starts on port `50051`.

### 4. Run the Client (in a separate terminal)

```bash
python client/client.py
```

The client automatically:

1. **Creates** an employee (Alice, Engineering)
2. **Gets** the employee by ID
3. **Lists** all employees

---

## 📝 Protobuf Definition

Defined in [`proto/employee.proto`](proto/employee.proto):

```protobuf
syntax = "proto3";

package employee;

service EmployeeService {
  rpc CreateEmployee (Employee) returns (EmployeeResponse);
  rpc GetEmployee (EmployeeId) returns (Employee);
  rpc ListEmployees (Empty) returns (EmployeeList);
}

message Empty {}

message EmployeeId {
  int32 id = 1;
}

message Employee {
  int32 id = 1;
  string name = 2;
  string email = 3;
  string department = 4;
}

message EmployeeResponse {
  string message = 1;
}

message EmployeeList {
  repeated Employee employees = 1;
}
```

---

## 🔍 How It Works

```
Client                                Server                  In-Memory Store
  │                                     │                           │
  │──Employee(Alice)───────────▸        │──store employee──────▸    │
  │    ◂──EmployeeResponse─────        │                           │
  │                                     │                           │
  │──EmployeeId(id=1)─────────▸        │──lookup by id────────▸    │
  │    ◂──Employee─────────────        │    ◂──employee────────    │
  │                                     │                           │
  │──Empty─────────────────────▸        │──list all─────────────▸   │
  │    ◂──EmployeeList─────────        │    ◂──[employees]─────    │
```

### Architecture

- **`server/server.py`** — Implements `EmployeeServiceServicer` with an in-memory dictionary (`EMPLOYEES`). The `CreateEmployee` RPC stores the employee protobuf directly; `GetEmployee` looks up by ID and returns `NOT_FOUND` if missing; `ListEmployees` returns all entries.
- **`client/client.py`** — Calls all three RPCs sequentially to demonstrate the full workflow.
- **`database/schema.sql`** — Reference SQL schema showing how the employee table could be modeled in a relational database.

### Error Handling

- `GetEmployee` returns `StatusCode.NOT_FOUND` with detail `"Employee not found"` when the ID doesn't exist.

---

## 📦 Dependencies

| Package        | Purpose                           |
|---------------|-----------------------------------|
| `grpcio`       | gRPC runtime                      |
| `grpcio-tools` | Protobuf compiler plugin for gRPC |

---

## 📄 License

This project is part of the [backend-engineering-playbook](../../../) and is intended for educational purposes.
