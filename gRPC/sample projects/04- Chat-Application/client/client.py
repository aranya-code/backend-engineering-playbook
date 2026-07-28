import grpc
import chat_pb2, chat_pb2_grpc

def messages():
    for text in ["Hello","How are you?","Goodbye"]:
        yield chat_pb2.ChatMessage(user="Alice", message=text)

with grpc.insecure_channel("localhost:50051") as channel:
    stub=chat_pb2_grpc.ChatServiceStub(channel)
    for reply in stub.Chat(messages()):
        print(f"[{reply.user}] {reply.message}")
