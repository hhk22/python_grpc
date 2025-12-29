from concurrent import futures

import grpc
import time

import data_service_pb2
import data_service_pb2_grpc


class DataService(data_service_pb2_grpc.DataServiceServicer):
    def GetData(self, request, context):
        data_id = request.data_id

        data = b"This is a test data" * 100000

        print(f"Data {len(data)} bytes")

        return data_service_pb2.DataResponse(data=data)


def serve():
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        compression=grpc.Compression.Gzip
    )

    data_service_pb2_grpc.add_DataServiceServicer_to_server(DataService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()