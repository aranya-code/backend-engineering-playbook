# Run

1. Create a virtual environment and install requirements.
2. Generate gRPC code:

```bash
python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/employee.proto
```

3. Run Django migrations.
4. Start the Django application.
5. Start the gRPC server.

This starter separates the Django application from the gRPC transport layer.
