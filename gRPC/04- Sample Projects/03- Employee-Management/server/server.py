from concurrent import futures
import grpc
# Generate employee_pb2.py and employee_pb2_grpc.py before running.
import employee_pb2, employee_pb2_grpc

EMPLOYEES={}

class Service(employee_pb2_grpc.EmployeeServiceServicer):
    def CreateEmployee(self, request, context):
        EMPLOYEES[request.id]=request
        return employee_pb2.EmployeeResponse(message="Employee created")
    def GetEmployee(self, request, context):
        if request.id not in EMPLOYEES:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Employee not found")
            return employee_pb2.Employee()
        return EMPLOYEES[request.id]
    def ListEmployees(self, request, context):
        return employee_pb2.EmployeeList(employees=list(EMPLOYEES.values()))

server=grpc.server(futures.ThreadPoolExecutor(max_workers=10))
employee_pb2_grpc.add_EmployeeServiceServicer_to_server(Service(),server)
server.add_insecure_port("[::]:50051")
server.start()
print("Employee service running on :50051")
server.wait_for_termination()
