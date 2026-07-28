# Run

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate

pip install -r requirements.txt

python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/calculator.proto

python server.py
```

In another terminal:

```bash
python client.py
```
