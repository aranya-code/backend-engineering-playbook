# Hello World gRPC Project

A minimal Python gRPC example demonstrating the simplest possible **Unary RPC** — a single request and a single response. This is the ideal starting point for learning gRPC with Python.

---

## 📡 RPC Pattern

| RPC Method   | Pattern    | Description                                      |
|-------------|-----------|--------------------------------------------------|
| `SayHello`  | **Unary** | Client sends a name, server replies with a greeting. |

---

## 📁 Project Structure

```
01- Hello-World/
├── proto/
│   └── hello.proto          # Protobuf service & message definitions
├── server.py                # gRPC server implementation
├── client.py                # gRPC client
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

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate Python Code from Proto

```bash
python -m grpc_tools.protoc -I proto --python_out=proto --grpc_python_out=proto proto/hello.proto
```

### 3. Start the Server

```bash
python server.py
```

The server starts on port `50051`.

### 4. Run the Client (in a separate terminal)

```bash
python client.py
```

**Expected output:**

```
Greeter client received: Hello, World!
```

---

## 📝 Protobuf Definition

Defined in [`proto/hello.proto`](proto/hello.proto):

```protobuf
syntax = "proto3";

package hello;

service Greeter {
  rpc SayHello (HelloRequest) returns (HelloReply);
}

message HelloRequest {
  string name = 1;
}

message HelloReply {
  string message = 1;
}
```

---

## 🔍 How It Works

```
Client                          Server
  │                               │
  │──HelloRequest(name)──────▸    │
  │                               │  Constructs greeting
  │    ◂──────HelloReply(message)─│
  │                               │
```

1. The **client** creates a `HelloRequest` with `name = "World"`.
2. The **server** receives the request and returns a `HelloReply` with `message = "Hello, World!"`.
3. The client prints the response.

---

## 📦 Dependencies

| Package        | Purpose                           |
|---------------|-----------------------------------|
| `grpcio`       | gRPC runtime                      |
| `grpcio-tools` | Protobuf compiler plugin for gRPC |
| `protobuf`     | Protocol Buffers runtime          |

---

## 📄 License

This project is part of the [backend-engineering-playbook](../../../) and is intended for educational purposes.
