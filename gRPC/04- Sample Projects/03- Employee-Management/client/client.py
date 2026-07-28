import grpc
import employee_pb2, employee_pb2_grpc
ch=grpc.insecure_channel("localhost:50051")
stub=employee_pb2_grpc.EmployeeServiceStub(ch)
stub.CreateEmployee(employee_pb2.Employee(id=1,name="Alice",email="alice@example.com",department="Engineering"))
print(stub.GetEmployee(employee_pb2.EmployeeId(id=1)))
print(stub.ListEmployees(employee_pb2.Empty()))
