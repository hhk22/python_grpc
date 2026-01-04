
from concurrent import futures

import retry_example_pb2
import retry_example_pb2_grpc

import time
import grpc


class ExampleService(retry_example_pb2_grpc.ExampleServiceServicer):
    def SayHello(self, request, context):
        if time.time() % 2 < 1:
            print("Server Unavailable")
            context.abort(grpc.StatusCode.UNAVAILABLE, "Server Unavailable")
        
        return retry_example_pb2.HelloReply(reply_message=f"Hello, {request.name}!")


def serve():

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    retry_example_pb2_grpc.add_ExampleServiceServicer_to_server(ExampleService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()