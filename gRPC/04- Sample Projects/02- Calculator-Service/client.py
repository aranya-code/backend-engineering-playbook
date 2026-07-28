import grpc
import calculator_pb2
import calculator_pb2_grpc

with grpc.insecure_channel("localhost:50051") as channel:
    stub = calculator_pb2_grpc.CalculatorStub(channel)
    req = calculator_pb2.BinaryOperationRequest(a=20, b=5)
    print("Add:", stub.Add(req).result)
    print("Subtract:", stub.Subtract(req).result)
    print("Multiply:", stub.Multiply(req).result)
    print("Divide:", stub.Divide(req).result)
