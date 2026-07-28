from concurrent import futures
import time

import grpc # type:ignore
import greet_pb2
import greet_pb2_grpc

class GreeterServicer(greet_pb2_grpc.GreeterServicer):
    def SayHello(self, request, context):
        print("Hello Request Made:")
        print(request)
        hello_reply = greet_pb2.Reply()
        hello_reply.greeting = f"{request.greeting} {request.name}"

        return hello_reply

    def ClientHello(self, request_iterator, context):
        MoreHello = greet_pb2.MoreHello()
        for request in request_iterator:
            print("ClientHello Request Made:")
            print(request)
            MoreHello.request.append(request)

        MoreHello.greeting = f"You have sent {len(MoreHello.request)} messages. Please expect a delayed response."
        return MoreHello

    
    def ServerHello(self, request, context):
        print("ServerHello Request Made:")
        print(request)

        for i in range(3):
            hello_reply = greet_pb2.Reply()
            hello_reply.greeting = f"{request.greeting} {request.name} {i + 1}"
            yield hello_reply
            time.sleep(3)


    def InteractiveHello(self, request_iterator, context):
        for request in request_iterator:
            print("InteractiveHello Request Made:")
            print(request)

            hello_reply = greet_pb2.Reply()
            hello_reply.greeting = f"{request.greeting} {request.name}"

            yield hello_reply

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    greet_pb2_grpc.add_GreeterServicer_to_server(GreeterServicer(), server)
    server.add_insecure_port("localhost:50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()