import greet_pb2_grpc
import greet_pb2
import time
import grpc #type:ignore

def get_client_stream_requests():
    while True:
        name = input("Please enter a name (or nothing to stop chatting): ")

        if name == "":
            break

        hello_request = greet_pb2.Hello(greeting = "Hello", name = name)
        yield hello_request
        time.sleep(1)

def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = greet_pb2_grpc.GreeterStub(channel)
        print("1. SayHello - Unary")
        print("2. ClientHello - Client Side Streaming")
        print("3. ServerHello - Server Side Streaming")        
        print("4. InteractiveHello - Both Streaming")
        rpc_call = input("Which rpc would you like to make: ")

        if rpc_call == "1":
            hello_request = greet_pb2.Hello(greeting = "Bonjour", name = "YouTube")
            hello_reply = stub.SayHello(hello_request)
            print("SayHello Response Received:")
            print(hello_reply)
        elif rpc_call == "2":
            delayed_reply = stub.ClientHello(get_client_stream_requests())

            print("ClientHello Response Received:")
            print(delayed_reply)
        elif rpc_call == "3":
            hello_request = greet_pb2.Hello(greeting = "Bonjour", name = "YouTube")
            hello_replies = stub.ServerHello(hello_request)

            for hello_reply in hello_replies:
                print("ServerHello Response Received:")
                print(hello_reply)
        elif rpc_call == "4":
            responses = stub.InteractiveHello(get_client_stream_requests())

            for response in responses:
                print("InteractiveHello Response Received: ")
                print(response)

if __name__ == "__main__":
    run()