from concurrent import futures
import grpc
import chat_pb2, chat_pb2_grpc

class Chat(chat_pb2_grpc.ChatServiceServicer):
    def Chat(self, request_iterator, context):
        for msg in request_iterator:
            print(f"[{msg.user}] {msg.message}")
            yield chat_pb2.ChatMessage(
                user="Server",
                message=f"Echo: {msg.message}"
            )

server=grpc.server(futures.ThreadPoolExecutor(max_workers=10))
chat_pb2_grpc.add_ChatServiceServicer_to_server(Chat(), server)
server.add_insecure_port("[::]:50051")
server.start()
print("Chat server running on :50051")
server.wait_for_termination()
