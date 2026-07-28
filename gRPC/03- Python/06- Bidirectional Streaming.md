# Overview

While Client Streaming allows multiple requests followed by a single response, and Server Streaming allows a single request followed by multiple responses, some applications require **both the client and the server to continuously exchange messages**.

Examples include:

- Chat applications
- Multiplayer games
- Live collaboration tools
- Video conferencing
- Real-time dashboards
- IoT device communication
- Financial trading platforms
- Interactive AI assistants

These applications cannot wait for one side to finish sending data before the other responds.

To support this communication pattern, gRPC provides **Bidirectional Streaming RPC**.

In a Bidirectional Streaming RPC, both the client and the server maintain independent streams. Each side can send messages whenever it chooses, and messages can flow simultaneously in both directions over a single HTTP/2 connection.

This chapter explains how Bidirectional Streaming works, how it is implemented in Python, and the scenarios where it provides the greatest value.

---

# What is Bidirectional Streaming?

A Bidirectional Streaming RPC allows:

- The client to send multiple requests.
- The server to send multiple responses.
- Both sides to communicate independently.
- Messages to flow simultaneously.

Communication flow:

```text
Client

Request 1

────────────►

                Response 1

◄────────────

Request 2

────────────►

                Response 2

◄────────────

Request 3

────────────►

                Response 3

◄────────────

...

Both streams remain open until either side closes them.
```

Unlike the previous RPC types, neither side needs to wait for the other before sending the next message.

---

# When Should You Use Bidirectional Streaming?

Bidirectional Streaming is useful whenever communication is continuous and interactive.

Common examples include:

- Chat systems
- Multiplayer gaming
- Live notifications
- GPS tracking
- IoT telemetry
- Voice assistants
- Live collaboration
- Financial trading systems
- Remote device control

It enables full-duplex communication between the client and server.

---

# Bidirectional Streaming Definition

A Bidirectional Streaming RPC uses the `stream` keyword for both the request and the response.

Example:

```proto
syntax = "proto3";

package chat;

service ChatService {

    rpc Chat(stream ChatMessage)
        returns (stream ChatMessage);

}

message ChatMessage {

    string user = 1;

    string message = 2;

}
```

Both request and response are streams.

---

# Understanding the RPC Definition

Consider:

```proto
rpc Chat(stream ChatMessage)
    returns (stream ChatMessage);
```

Breaking it down:

| Component | Description |
|-----------|-------------|
| Chat | RPC method |
| stream ChatMessage | Multiple client requests |
| stream ChatMessage | Multiple server responses |

Both sides communicate using the same message type.

---

# Communication Lifecycle

A Bidirectional Streaming RPC follows this sequence.

```text
Client

        │

Send Message

────────────►

        │

Receive Reply

◄────────────

        │

Send Message

────────────►

        │

Receive Reply

◄────────────

        │

...

Both streams remain active.
```

The client and server operate independently.

---

# Generated Python Classes

Python generates the usual files.

```text
chat_pb2.py

chat_pb2_grpc.py
```

The generated service interface supports streaming in both directions.

---

# Implementing the Server

The server receives an iterator of incoming messages and yields responses.

```python
import chat_pb2
import chat_pb2_grpc


class ChatService(chat_pb2_grpc.ChatServiceServicer):

    def Chat(self, request_iterator, context):

        for message in request_iterator:

            yield chat_pb2.ChatMessage(
                user="Server",
                message=f"Received: {message.message}"
            )
```

The server processes each incoming message and immediately sends a response.

---

# Understanding `request_iterator`

The incoming messages arrive as an iterator.

```python
for message in request_iterator:

    ...
```

Each iteration retrieves the next message from the client.

The server does not need to wait for the entire stream before responding.

---

# Using `yield`

Responses are sent using `yield`.

```python
yield chat_pb2.ChatMessage(...)
```

Each yielded message is immediately transmitted to the client.

This allows real-time interaction.

---

# Registering the Service

Service registration remains unchanged.

```python
chat_pb2_grpc.add_ChatServiceServicer_to_server(
    ChatService(),
    server
)
```

---

# Implementing the Client

The client produces a stream of outgoing messages.

```python
def message_generator():

    messages = [

        "Hello",

        "How are you?",

        "Goodbye"

    ]

    for text in messages:

        yield chat_pb2.ChatMessage(

            user="Alice",

            message=text

        )
```

The generator yields one message at a time.

---

# Sending and Receiving Messages

Create the stub.

```python
channel = grpc.insecure_channel("localhost:50051")

stub = chat_pb2_grpc.ChatServiceStub(channel)
```

Start the stream.

```python
responses = stub.Chat(
    message_generator()
)
```

The client can now receive responses as they arrive.

```python
for response in responses:

    print(response.user)

    print(response.message)
```

Output:

```text
Server

Received: Hello

Server

Received: How are you?

Server

Received: Goodbye
```

---

# Bidirectional Communication Timeline

```text
Client                      Server

Message 1  ───────────────►

             ◄──────────── Reply 1

Message 2  ───────────────►

             ◄──────────── Reply 2

Message 3  ───────────────►

             ◄──────────── Reply 3

...

Connection remains open.
```

Messages travel independently in both directions.

---

# Bidirectional Streaming vs Other RPC Types

| RPC Type | Client Requests | Server Responses |
|-----------|----------------:|-----------------:|
| Unary | 1 | 1 |
| Server Streaming | 1 | Many |
| Client Streaming | Many | 1 |
| Bidirectional Streaming | Many | Many |

Bidirectional Streaming is the most flexible communication model provided by gRPC.

---

# Handling Errors

Errors can occur at any point during the stream.

Example:

```text
Client

Message

────────────►

Server

Processing Error

◄────────────

INTERNAL
```

When an unrecoverable error occurs, both streams are terminated and the client receives a gRPC exception.

Applications should handle these exceptions gracefully.

---

# Real-World Example

A chat application is a classic use case.

```proto
service ChatService {

    rpc Chat(stream ChatMessage)
        returns (stream ChatMessage);

}
```

Communication might look like:

```text
Alice: Hello

Bob: Hi!

Alice: How are you?

Bob: I'm doing well.

Alice: Great!
```

Neither participant waits for the other to finish the conversation.

---

# Advantages of Bidirectional Streaming

Bidirectional Streaming offers several benefits.

- Real-time communication
- Low latency
- Efficient network utilization
- Single persistent connection
- Reduced connection overhead
- Supports interactive applications
- Ideal for continuous message exchange

---

# When Should You Avoid Bidirectional Streaming?

Bidirectional Streaming may not be appropriate when:

- Only one request and one response are required.
- Data flows in only one direction.
- The added complexity is unnecessary.
- The application follows a simple CRUD pattern.

In these cases, Unary or one-way streaming RPCs are simpler and easier to maintain.

---

# Best Practices

- Keep streamed messages small.
- Process messages as they arrive.
- Handle client cancellations using the gRPC context.
- Validate incoming messages before processing.
- Return meaningful status codes when errors occur.
- Avoid blocking operations inside the streaming loop.
- Monitor long-lived streams for resource usage.

---

# Common Mistakes

Avoid the following mistakes:

- Waiting for the client stream to finish before sending responses.
- Loading the entire request stream into memory.
- Ignoring client disconnections.
- Sending oversized messages.
- Performing long-running blocking operations inside the stream.
- Using Bidirectional Streaming when a simpler RPC type is sufficient.

---

# Key Takeaways

- Bidirectional Streaming allows both the client and server to exchange multiple messages independently.
- Both the request and response types are declared with the `stream` keyword.
- Python servers receive streamed requests through an iterator and send responses using `yield`.
- Clients send a stream of messages while simultaneously receiving streamed responses.
- Bidirectional Streaming is ideal for chat systems, real-time collaboration, IoT communication, gaming, and other interactive applications.
- It is the most flexible and powerful communication pattern available in gRPC.