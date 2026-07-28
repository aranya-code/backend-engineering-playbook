## To compile python grpc proto file
python -m grpc_tools.protoc -I protos --python_out=. --grpc_python_out=. protos/greet.proto

## Activating virtual environment
venv\scripts\activate

## Running the server
python -m server.greet_server

## Running the client
python -m client.greet_client