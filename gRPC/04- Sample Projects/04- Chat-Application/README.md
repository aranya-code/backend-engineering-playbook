# Chat Application (gRPC Bidirectional Streaming)

A chat application built with Python gRPC using **Bidirectional Streaming**. The client sends a stream of messages and the server echoes each one back, demonstrating simultaneous streaming in both directions.

---

## 📡 RPC Pattern

| RPC Method | Pattern                      | Description                                                  |
|-----------|-----------------------------|------------------------------------------------------------|
| `Chat`    | **Bidirectional Streaming** | Client streams messages in; server echoes each one back.    |

---

## 📁 Project Structure

```
04- Chat-Application/
├── proto/
│   └── chat.proto              # Protobuf service & message definitions
├── server/
│   └── server.py               # gRPC chat server (echo-style)
├── client/
│   └── client.py               # gRPC chat client
├── requirements.txt            # Python dependencies
├── run.md                      # Quick-run commands
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
python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/chat.proto
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

---

## 📝 Protobuf Definition

Defined in [`proto/chat.proto`](proto/chat.proto):

```protobuf
syntax = "proto3";

package chat;

service ChatService {
  rpc Chat (stream ChatMessage) returns (stream ChatMessage);
}

message ChatMessage {
  string user = 1;
  string message = 2;
}
```

---

## 🔍 How It Works

```
Client (Alice)                  Server
   │                              │
   │──ChatMessage("Hello")───▸    │
   │    ◂──"Echo: Hello"─────    │
   │                              │
   │──ChatMessage("How are you?")─▸│
   │    ◂──"Echo: How are you?"──│
   │                              │
   │──ChatMessage("Goodbye")──▸   │
   │    ◂──"Echo: Goodbye"────   │
```

### Architecture

- **Server (`server/server.py`)** — Implements `ChatServiceServicer`. For each incoming `ChatMessage`, the server logs it and yields a reply with `user = "Server"` and `message = "Echo: <original>"`.
- **Client (`client/client.py`)** — Sends a predefined sequence of messages ("Hello", "How are you?", "Goodbye") as `user = "Alice"`, then prints each echoed reply.

### Key Concepts Demonstrated

- **Bidirectional streaming** — Both client and server use streaming. The client sends a stream of `ChatMessage` objects via a generator, and the server yields back a `ChatMessage` for each received message.
- **Generator-based streaming** — The client's `messages()` generator function produces the outgoing stream.

---

## 💬 Example Session

**Server terminal:**
```
Chat server running on :50051
[Alice] Hello
[Alice] How are you?
[Alice] Goodbye
```

**Client terminal:**
```
[Server] Echo: Hello
[Server] Echo: How are you?
[Server] Echo: Goodbye
```

---

## 📦 Dependencies

| Package        | Purpose                           |
|---------------|-----------------------------------|
| `grpcio`       | gRPC runtime                      |
| `grpcio-tools` | Protobuf compiler plugin for gRPC |

---

## 📄 License

This project is part of the [backend-engineering-playbook](../../../) and is intended for educational purposes.
