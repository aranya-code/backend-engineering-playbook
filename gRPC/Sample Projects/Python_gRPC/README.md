# Python gRPC — Greeter Service

A sample Python gRPC project demonstrating all four gRPC communication patterns using a simple **Greeter** service.

---

## 📡 RPC Patterns Covered

| #  | RPC Method          | Pattern                    | Description                                                  |
|----|---------------------|----------------------------|--------------------------------------------------------------|
| 1  | `SayHello`          | **Unary**                  | Client sends one request, server returns one response.       |
| 2  | `ClientHello`       | **Client Streaming**       | Client streams multiple requests, server returns one response. |
| 3  | `ServerHello`       | **Server Streaming**       | Client sends one request, server streams multiple responses. |
| 4  | `InteractiveHello`  | **Bidirectional Streaming** | Both client and server stream messages simultaneously.       |

---

## 📁 Project Structure

```
Python_gRPC/
├── protos/
│   └── greet.proto            # Protobuf service & message definitions
├── server/
│   └── greet_server.py        # gRPC server implementation
├── client/
│   └── greet_client.py        # Interactive gRPC client
├── greet_pb2.py               # Generated protobuf message code (do not edit)
├── greet_pb2_grpc.py          # Generated gRPC stub/servicer code (do not edit)
├── requirements.txt           # Python dependencies
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
# Create
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS / Linux)
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. (Optional) Regenerate Protobuf / gRPC Code

The generated files (`greet_pb2.py`, `greet_pb2_grpc.py`) are already included. If you modify `greet.proto`, regenerate them with:

```bash
python -m grpc_tools.protoc -I protos --python_out=. --grpc_python_out=. protos/greet.proto
```

### 4. Start the Server

```bash
python -m server.greet_server
```

The server starts on `localhost:50051`.

### 5. Run the Client (in a separate terminal)

```bash
python -m client.greet_client
```

You'll see an interactive menu:

```
1. SayHello - Unary
2. ClientHello - Client Side Streaming
3. ServerHello - Server Side Streaming
4. InteractiveHello - Both Streaming
Which rpc would you like to make:
```

---

## 📝 Protobuf Definitions

Defined in [`protos/greet.proto`](protos/greet.proto):

### Messages

```protobuf
// Request
message Hello {
  string name = 1;
  string greeting = 2;
}

// Response
message Reply {
  string greeting = 1;
}

// Aggregated response (used by ClientHello)
message MoreHello {
  string greeting = 1;
  repeated Hello request = 2;
}
```

### Service

```protobuf
service Greeter {
  rpc SayHello (Hello) returns (Reply);                        // Unary
  rpc ClientHello (stream Hello) returns (MoreHello);          // Client Streaming
  rpc ServerHello (Hello) returns (stream Reply);              // Server Streaming
  rpc InteractiveHello (stream Hello) returns (stream Reply);  // Bidirectional
}
```

---

## 🔍 RPC Details

### 1 — Unary: `SayHello`

The client sends a single `Hello` message and receives a single `Reply`.

```
Client  ──Hello──▸  Server
Client  ◂──Reply──  Server
```

### 2 — Client Streaming: `ClientHello`

The client streams multiple `Hello` messages. Once the stream ends, the server responds with a single `MoreHello` containing all received requests.

```
Client  ──Hello──▸
Client  ──Hello──▸  Server
Client  ──Hello──▸
Client  ◂─MoreHello─  Server
```

### 3 — Server Streaming: `ServerHello`

The client sends one `Hello`. The server responds with a stream of 3 `Reply` messages, each 3 seconds apart.

```
Client  ──Hello──▸  Server
Client  ◂──Reply──  Server  (x3, 3s interval)
```

### 4 — Bidirectional Streaming: `InteractiveHello`

Both sides stream simultaneously. For each `Hello` the client sends, the server immediately yields a `Reply`.

```
Client  ──Hello──▸  Server
Client  ◂──Reply──  Server
Client  ──Hello──▸  Server
Client  ◂──Reply──  Server
        ...
```

---

## 📦 Dependencies

| Package              | Version  | Purpose                            |
|----------------------|----------|------------------------------------|
| `grpcio`             | 1.83.0   | gRPC runtime                       |
| `grpcio-tools`       | 1.83.0   | Protobuf compiler plugin for gRPC  |
| `protobuf`           | 7.35.1   | Protocol Buffers runtime           |
| `setuptools`         | 83.0.0   | Build utilities                    |
| `typing_extensions`  | 4.16.0   | Backported typing features         |

---

## 📄 License

This project is part of the [backend-engineering-playbook](../../) and is intended for educational purposes.
