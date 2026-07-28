# Run

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt

python -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/hello.proto

python server.py
```

Open another terminal:

```bash
python client.py
```
