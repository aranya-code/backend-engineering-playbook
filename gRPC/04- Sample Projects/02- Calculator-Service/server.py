from concurrent import futures
import grpc
import calculator_pb2
import calculator_pb2_grpc

class Calculator(calculator_pb2_grpc.CalculatorServicer):
    def Add(self, request, context):
        return calculator_pb2.OperationReply(result=request.a + request.b)
    def Subtract(self, request, context):
        return calculator_pb2.OperationReply(result=request.a - request.b)
    def Multiply(self, request, context):
        return calculator_pb2.OperationReply(result=request.a * request.b)
    def Divide(self, request, context):
        if request.b == 0:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Division by zero is not allowed.")
            return calculator_pb2.OperationReply()
        return calculator_pb2.OperationReply(result=request.a / request.b)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=5))
    calculator_pb2_grpc.add_CalculatorServicer_to_server(Calculator(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("Calculator server listening on :50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
