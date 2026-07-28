# Run

1. Install dependencies.
2. Generate Python code:

```bash
python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/chat.proto
```

3. Start the server:

```bash
python server/server.py
```

4. Run one or more clients:

```bash
python client/client.py
```
