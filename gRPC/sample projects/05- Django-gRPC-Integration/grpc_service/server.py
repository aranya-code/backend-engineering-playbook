from concurrent import futures
import grpc
import employee_pb2
import employee_pb2_grpc

class EmployeeService(employee_pb2_grpc.EmployeeServiceServicer):
    def GetEmployee(self, request, context):
        # Placeholder. In a real project this would query Django ORM.
        return employee_pb2.EmployeeResponse(
            id=request.id,
            name="Demo User",
            email="demo@example.com"
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    employee_pb2_grpc.add_EmployeeServiceServicer_to_server(EmployeeService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("gRPC server listening on :50051")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
