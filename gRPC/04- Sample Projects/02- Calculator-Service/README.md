# Calculator Service (gRPC)

A Python gRPC project implementing a **Calculator** service with four **Unary RPC** operations — Add, Subtract, Multiply, and Divide. Demonstrates error handling for division by zero using gRPC status codes.

---

## 📡 RPC Methods

| RPC Method   | Pattern    | Description                                                     |
|-------------|-----------|----------------------------------------------------------------|
| `Add`       | **Unary** | Returns `a + b`                                                 |
| `Subtract`  | **Unary** | Returns `a - b`                                                 |
| `Multiply`  | **Unary** | Returns `a * b`                                                 |
| `Divide`    | **Unary** | Returns `a / b` (returns `INVALID_ARGUMENT` on division by zero)|

---

## 📁 Project Structure

```
02- Calculator-Service/
├── proto/
│   └── calculator.proto     # Protobuf service & message definitions
├── server.py                # gRPC server with calculator logic
├── client.py                # gRPC client that calls all operations
├── requirements.txt         # Python dependencies
├── run.md                   # Quick-run commands
├── .gitignore
└── README.md
```

---

## 🛠️ Prerequisites

- **Python 3.8+**
- **pip**

---

## 🚀 Getting Started

### 1. Create & Activate a Virtual Environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Generate Python Code from Proto

```bash
python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/calculator.proto
```

### 4. Start the Server

```bash
python server.py
```

The server starts on port `50051`.

### 5. Run the Client (in a separate terminal)

```bash
python client.py
```

**Expected output (with `a=20`, `b=5`):**

```
Add: 25.0
Subtract: 15.0
Multiply: 100.0
Divide: 4.0
```

---

## 📝 Protobuf Definition

Defined in [`proto/calculator.proto`](proto/calculator.proto):

```protobuf
syntax = "proto3";

package calculator;

service Calculator {
  rpc Add (BinaryOperationRequest) returns (OperationReply);
  rpc Subtract (BinaryOperationRequest) returns (OperationReply);
  rpc Multiply (BinaryOperationRequest) returns (OperationReply);
  rpc Divide (BinaryOperationRequest) returns (OperationReply);
}

message BinaryOperationRequest {
  double a = 1;
  double b = 2;
}

message OperationReply {
  double result = 1;
}
```

---

## 🔍 How It Works

```
Client                                   Server
  │                                        │
  │──BinaryOperationRequest(20, 5)──▸ Add  │  → 25.0
  │──BinaryOperationRequest(20, 5)──▸ Sub  │  → 15.0
  │──BinaryOperationRequest(20, 5)──▸ Mul  │  → 100.0
  │──BinaryOperationRequest(20, 5)──▸ Div  │  → 4.0
  │                                        │
  │    ◂──OperationReply(result)───────────│
  │                                        │
```

- All four operations are **Unary RPCs** — one request in, one response out.
- **Division by zero** is handled with `grpc.StatusCode.INVALID_ARGUMENT`, demonstrating proper gRPC error handling.

---

## ⚠️ Error Handling

When `b = 0` is passed to the `Divide` RPC:

- The server sets `StatusCode.INVALID_ARGUMENT` with detail `"Division by zero is not allowed."`.
- The client receives a `grpc.RpcError` with the corresponding status.

---

## 📦 Dependencies

| Package        | Purpose                           |
|---------------|-----------------------------------|
| `grpcio`       | gRPC runtime                      |
| `grpcio-tools` | Protobuf compiler plugin for gRPC |

---

## 📄 License

This project is part of the [backend-engineering-playbook](../../../) and is intended for educational purposes.
